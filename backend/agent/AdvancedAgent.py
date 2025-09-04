"""
AdvancedAgent.py
LangGraph ReAct + MCP Banking Agent

- customer_id tool çağrılarına ZORUNLU enjekte edilir (alias denemeli):
  customer_id | customerId | user_id | customer
- Eğer tool şeması belirli bir ismi bekliyorsa, ValidationError "unexpected keyword"
  alınırsa ajan otomatik olarak sıradaki alias'ı dener ve RETRY yapar.
- Planlı akışta "bakiye" için:
    1) get_accounts (customer_id ile)
    2) tek hesapsa doğrudan get_balance (account_id ile)
    3) >1 hesapsa seçtirme (requires_disambiguation + UI)
- ReAct fallback yine mevcut; ancak planlı akış başarı şansı yüksek olduğu için
  modelin "müşteri id iste" demesine fırsat kalmaz.
- Yanıtlar normalize: {"text","YANIT","ui_component"}
"""

from __future__ import annotations
import os, re, json, logging, asyncio
from typing import Any, Dict, List, Optional, Tuple

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain.tools import StructuredTool
from langgraph.prebuilt import create_react_agent
from langchain_mcp_adapters.client import MultiServerMCPClient


# ================ Logger ==================
log = logging.getLogger("advanced-agent")
if not log.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter("%(message)s"))
    log.addHandler(h)
log.setLevel(logging.INFO)

# # ================= Config =================
try:
    from config_local import LLM_API_BASE, LLM_MODEL
    from config_local import LLM_API_KEY as HF_API_KEY
    from config_local import MCP_SSE_URL as MCP_URL
except Exception as e:
     log.error(json.dumps({"event":"config_init_error","error":str(e)}))

def _mask(s: str) -> str:
    if not isinstance(s, str):
        return s
    s = re.sub(r'\bTR\d{20,26}\b', 'TR************', s, flags=re.IGNORECASE)
    s = re.sub(r'\b\d{11,}\b', '***', s)
    s = re.sub(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', '***@***', s)
    return s

# =================== Agent ===================
class BankingAgent:
    CUSTOMER_ALIASES = ("customer_id", "customerId", "user_id", "customer")

    def __init__(self, mcp_url: str = MCP_URL):
        self.mcp_url = mcp_url
        self.client: Optional[MultiServerMCPClient] = None
        self.raw_tools: List[Any] = []
        self.tools_wrapped: List[Any] = []
        self.agent = None
        self.model: Optional[ChatOpenAI] = None
        self.customer_id: Optional[int] = None
        self.session_id: Optional[str] = None
        self.TOOL_TIMEOUT_SECONDS: float = 4.0

        self.system_prompt = (
            "You are InterChat, a secure banking assistant. Use tools; don't ask for secrets.\n"
            "Türk kullanıcıya Türkçe, kısa ve net cevap ver.\n"
            "Hesap seçimi gerekiyorsa tool'ların döndürdüğü listeyi kullan; kendin müşteri kimlik isteme.\n"
            "Asla <think> veya herhangi bir düşünme içeriğini kullanıcıya yazma; sadece nihai cevabı ver.\n"
            "Customer ID otomatik olarak tool'lara eklenir, kullanıcıdan isteme.\n\n"
            "ÖNEMLİ: Kullanıcı işlem geçmişi (transactions) istiyorsa ama hangi hesabı belirtmemişse, önce hangi hesabın işlem geçmişini göstermek istediğini sor. "
            "Hesap numarası belirtilmeden işlem geçmişi gösterme. Kullanıcı hesap belirttikten sonra transactions_list tool'unu kullan."
        )

    # ---------- lifecycle ----------
    async def initialize(self) -> bool:
        try:
            if not HF_API_KEY:
                log.warning(json.dumps({"event":"warn","message":"HF_API_KEY yok (ENV)."}))

            self.model = ChatOpenAI(
                model=LLM_MODEL,
                openai_api_base=LLM_API_BASE,
                openai_api_key=HF_API_KEY,
                temperature=0.2,
                max_tokens=2048,
                max_retries=2,
                timeout=15,
            )
            self.client = MultiServerMCPClient({
                "fortuna_banking": {"url": self.mcp_url, "transport": "sse"}
            })
            self.raw_tools = await self.client.get_tools()

            # ReAct için wrap (LLM seçerse de customer_id enjekte edelim)
            self.tools_wrapped = self._wrap_tools_with_context(self.raw_tools)
            self.agent = create_react_agent(model=self.model, tools=self.tools_wrapped)
            return True
        except Exception as e:
            log.error(json.dumps({"event":"agent_init_error","error":str(e)}))
            return False

    async def run(self, user_message: str, *, customer_id: Optional[int] = None, session_id: Optional[str] = None) -> Dict[str, Any]:
        self.customer_id = customer_id
        self.session_id = session_id
        self.last_user_text = user_message

        # her çalıştırmada ajanı yeniden kurma; yalnızca last_user_text güncellenir

        log.info(json.dumps({"event":"chat_request","msg_masked":_mask(user_message),"customer_id":customer_id}))

        # LLM'in otomatik tool seçimi yapmasını sağla - manuel intent tespiti yok
        result = await self._react(user_message)

        # _react'ten dönen yanıtı kontrol et
        if isinstance(result, dict) and "tool_output" in result:
            # Tool yanıtı varsa, intent ile birlikte format et
            final = self._format_output(result.get("intent"), result["tool_output"])
        else:
            # Normal yanıt
            final = self._format_output(None, result)
        log.info(json.dumps({"event":"chat_response","resp_masked":_mask(final.get('text','')),"has_ui": bool(final.get('ui_component'))}))
        return final

    # ---------- wrap (LLM seçerse de customer_id ekle) ----------
    def _wrap_tools_with_context(self, tools: List[Any]):
        wrapped = []
        for t in tools:
            name = getattr(t, "name", "mcp_tool")
            desc = getattr(t, "description", "") or ""
            args_schema = getattr(t, "args_schema", None)

            async def _acall(*, _t=t, _name=name, _args_schema=args_schema, **kwargs):
                payload = dict(kwargs or {})

                # Transactions niyeti sırasında 'get_accounts' çağrılarını veto et
                try:
                    txt = (self.last_user_text or "").lower()
                    is_transactions_intent = any(w in txt for w in ["işlem", "hareket", "transaction", "transactions"]) and not any(w in txt for w in ["bakiye", "balance"]) 
                    if is_transactions_intent and _name.lower() in ("get_accounts", "accounts.list", "list_accounts"):
                        ask = "Hangi hesabın işlem geçmişini listeleyeyim? Örn: 'hesap 123 son işlemler'"
                        return {"ok": True, "YANIT": ask, "text": ask}
                except Exception:
                    pass
                
                # "en yakın" niyeti: branch_atm_search için nearby=True ekle
                try:
                    txt_low = (self.last_user_text or "").lower()
                    wants_nearby = any(k in txt_low for k in ["en yakın", "en yakin", "yakın", "yakin", "yakindaki", "yakındaki", "civarında"]) and ("atm" in txt_low or "şube" in txt_low or "sube" in txt_low)
                except Exception:
                    wants_nearby = False
                try:
                    if wants_nearby and _name and str(_name).lower() == "branch_atm_search":
                        payload.setdefault("nearby", True)
                except Exception:
                    pass

                # Tool'un customer parametresi kabul edip etmediğini kontrol et
                tool_accepts_customer = False
                if _args_schema:
                    if hasattr(_args_schema, "model_fields"):
                        tool_accepts_customer = any(
                            alias in _args_schema.model_fields 
                            for alias in self.CUSTOMER_ALIASES
                        )
                    elif hasattr(_args_schema, "properties"):
                        tool_accepts_customer = any(
                            alias in _args_schema.properties 
                            for alias in self.CUSTOMER_ALIASES
                        )
                
                # LLM tool seçse de ben customer_id'yi basarım (aliasları sırayla denerim)
                if self.customer_id is not None and tool_accepts_customer and not any(k in payload for k in self.CUSTOMER_ALIASES):
                    # En güvenlisi: tool çağrısını güvenli fonksiyonla yap (retry/alias)
                    try:
                        return await self._call_tool_with_customer("fortuna_banking", _name, payload)
                    except Exception as ex:
                        return {"ok": False, "error": f"tool_failed:{_name}:{ex}", "data": None}
                # Zaten müşteri alanı varsa veya tool customer kabul etmiyorsa doğrudan çağır
                try:
                    if hasattr(_t, "ainvoke"):
                        return await asyncio.wait_for(_t.ainvoke(payload), timeout=self.TOOL_TIMEOUT_SECONDS)
                    return await asyncio.wait_for(asyncio.to_thread(_t.invoke, payload), timeout=self.TOOL_TIMEOUT_SECONDS)
                except Exception as ex:
                    return {"ok": False, "error": f"tool_failed:{_name}:{ex}", "data": None}

            wrapped.append(
                StructuredTool.from_function(
                    name=name,
                    description=desc,
                    func=lambda **_: {"error": "use_async"},
                    coroutine=_acall,
                    args_schema=args_schema
                )
            )
        return wrapped

    # ---------- güvenli çağrı: customer_id alias RETRY ----------
    async def _call_tool_with_customer(self, server_name: str, tool_name: str, base_args: Dict[str, Any]) -> Any:
        """
        Tool'u customer_id ile çağırmayı GARANTİ eder.
        Şu sırayla dener: customer_id, customerId, user_id, customer.
        Eğer 'unexpected keyword' hatası alırsa bir sonraki alias ile tekrar dener.
        En son, alias eklemeden de dener (son çare).
        """
        last_exc = None
        tried_payloads = []

        # Tool'u bul
        target_tool = None
        for tool in self.raw_tools:
            if getattr(tool, "name", "") == tool_name:
                target_tool = tool
                break
        
        if not target_tool:
            raise RuntimeError(f"Tool '{tool_name}' not found")

        # Tool'un parametrelerini kontrol et
        args_schema = getattr(target_tool, "args_schema", None)
        tool_accepts_customer = False
        
        if args_schema:
            # args_schema'dan parametreleri kontrol et
            if hasattr(args_schema, "model_fields"):
                tool_accepts_customer = any(
                    alias in args_schema.model_fields 
                    for alias in self.CUSTOMER_ALIASES
                )
            elif hasattr(args_schema, "properties"):
                tool_accepts_customer = any(
                    alias in args_schema.properties 
                    for alias in self.CUSTOMER_ALIASES
                )

        # Eğer tool customer parametresi kabul etmiyorsa, sadece base_args'i kullan
        if not tool_accepts_customer:
            payload = dict(base_args or {})
            tried_payloads.append({"alias": None, "keys": list(payload.keys())})
            try:
                if hasattr(target_tool, "ainvoke"):
                    return await asyncio.wait_for(target_tool.ainvoke(payload), timeout=self.TOOL_TIMEOUT_SECONDS)
                else:
                    return await asyncio.wait_for(asyncio.to_thread(target_tool.invoke, payload), timeout=self.TOOL_TIMEOUT_SECONDS)
            except Exception as e:
                last_exc = e
        else:
            # Tool customer parametresi kabul ediyorsa, alias'ları dene
            for alias in self.CUSTOMER_ALIASES:
                payload = dict(base_args or {})
                if self.customer_id is not None and alias not in payload and not any(k in payload for k in self.CUSTOMER_ALIASES):
                    payload[alias] = self.customer_id
                tried_payloads.append({"alias": alias, "keys": list(payload.keys())})
                try:
                    # Tool'u doğrudan invoke et
                    if hasattr(target_tool, "ainvoke"):
                        return await asyncio.wait_for(target_tool.ainvoke(payload), timeout=self.TOOL_TIMEOUT_SECONDS)
                    else:
                        return await asyncio.wait_for(asyncio.to_thread(target_tool.invoke, payload), timeout=self.TOOL_TIMEOUT_SECONDS)
                except Exception as e:
                    msg = str(e).lower()
                    # sadece alias uyumsuzluğu ise sonraki alias'a geç
                    if "unexpected keyword" in msg or "validationerror" in msg:
                        last_exc = e
                        continue
                    # başka tür hata ise dur
                    last_exc = e
                    break

            # 2) son çare: alias eklemeden dene
            if last_exc is not None:
                try:
                    payload = dict(base_args or {})
                    tried_payloads.append({"alias": None, "keys": list(payload.keys())})
                    # Tool'u doğrudan invoke et
                    if hasattr(target_tool, "ainvoke"):
                        return await asyncio.wait_for(target_tool.ainvoke(payload), timeout=self.TOOL_TIMEOUT_SECONDS)
                    else:
                        return await asyncio.wait_for(asyncio.to_thread(target_tool.invoke, payload), timeout=self.TOOL_TIMEOUT_SECONDS)
                except Exception as e2:
                    last_exc = e2

        log.error(json.dumps({
            "event": "tool_call_failed_all_alias",
            "tool": tool_name,
            "tried": tried_payloads,
            "error": str(last_exc) if last_exc else "unknown"
        }))
        raise last_exc if last_exc else RuntimeError("tool_call_failed")

    # ---------- tool keşfi ----------
    def _find_tool_name(self, *candidates: str) -> Optional[str]:
        """
        Aday adları veya parça eşleşmelerini dener.
        Örn: "get_accounts", "accounts.list", "list_accounts"
        """
        cand = [c for c in candidates if c]
        # önce tam eşleşme
        for t in self.raw_tools:
            name = getattr(t, "name", "")
            if name in cand:
                return name
        # sonra parça eşleşme
        for t in self.raw_tools:
            name = (getattr(t, "name", "") or "").lower()
            desc = (getattr(t, "description", "") or "").lower()
            blob = f"{name} {desc}"
            if all(c.lower() in blob for c in cand):
                return getattr(t, "name", "")
        return None

    # ---------- format ----------
    def _format_output(self, intent: Optional[str], tool_output: Any) -> Dict[str, Any]:
        print(f"=== DEBUG: _format_output ===")
        print(f"intent: {intent}")
        print(f"tool_output type: {type(tool_output)}")
        print(f"tool_output: {tool_output}")
        
        # Hata durumlarını kullanıcıya anlamlı ilet
        if isinstance(tool_output, dict) and tool_output.get("error"):
            err = str(tool_output.get("error"))
            if "required property" in err or "validation" in err:
                msg = "Hesap bilgisi bulunamadı."
            elif "forbidden" in err or "403" in err or "erişim" in err:
                msg = "Bu hesap için erişim izniniz yok."
            else:
                msg = err
            return {"text": msg, "YANIT": msg, "ui_component": None}
        
        # Transactions niyeti için: hesap listesi dönerse bastır ve hesap sor
        try:
            if intent == "transactions" and isinstance(tool_output, dict):
                data = tool_output.get("data") if "data" in tool_output else tool_output
                ui = tool_output.get("ui_component") or (isinstance(data, dict) and data.get("ui_component"))
                has_accounts = False
                if isinstance(data, dict):
                    if isinstance(data.get("accounts"), list) and len(data.get("accounts")) > 0:
                        has_accounts = True
                # bazı araçlar doğrudan balance_card UI döndürür
                if not has_accounts and isinstance(ui, dict) and ui.get("type") == "balance_card":
                    has_accounts = True
                if has_accounts:
                    ask = "Hangi hesabın işlem geçmişini listeleyeyim? Örn: 'hesap 123 son işlemler'"
                    return {"text": ask, "YANIT": ask}
        except Exception:
            pass

        if isinstance(tool_output, dict):
            ui = tool_output.get("ui_component")
            data = tool_output.get("data") if "data" in tool_output else tool_output
            
            # UI component data içinde de olabilir (nested data yapısı için)
            if not ui and isinstance(data, dict):
                ui = data.get("ui_component")
                # Eğer data.data varsa, orada da ara
                if not ui and "data" in data and isinstance(data["data"], dict):
                    ui = data["data"].get("ui_component")

            if isinstance(data, dict) and data.get("requires_disambiguation"):
                # Seçtirme mesajı
                if data.get("accounts"):
                    items = data["accounts"]
                    ex = ", ".join(str(it.get("account_id") or it.get("id")) for it in items[:3])
                    text = f"{len(items)} hesabınız var. Hangi hesabı kullanayım? Örn: {ex}"
                    return {"text": text, "YANIT": text, "ui_component": ui}
                if data.get("cards"):
                    items = data["cards"]
                    ex = ", ".join(str(it.get("card_id") or it.get("id")) for it in items[:3])
                    text = f"{len(items)} kartınız var. Hangi kartı kullanayım? Örn: {ex}"
                    return {"text": text, "YANIT": text, "ui_component": ui}

            # Balance intent için özel işleme - UI component'ı koru
            if intent == "balance":
                # UI component varsa, onu kullan
                if ui:
                    # UI component'ı direkt döndür
                    txt = tool_output.get("YANIT") or tool_output.get("text") or tool_output.get("response") or "Hesap bakiyeniz şu şekildedir:"
                    return {"text": txt, "YANIT": txt, "ui_component": ui}
                
                # Eski format için fallback
                if isinstance(data, dict) and "balance" in data:
                    bal = data["balance"]; ccy = data.get("currency","TRY")
                    acc = data.get("account_id"); last4 = (data.get("iban") or "")[-4:]
                    text = f"Hesap {acc} ({last4}) bakiyeniz: {bal} {ccy}."
                    return {"text": text, "YANIT": text, "ui_component": ui}

            # Genel tool yanıtları için - UI component'ı koru
            if ui:
                # UI component varsa, onu kullan
                # Metni hem 'data' içinden hem de ana çıktıdan ara
                txt = (data.get("YANIT") if isinstance(data, dict) else None) or \
                      (data.get("text") if isinstance(data, dict) else None) or \
                      tool_output.get("YANIT") or \
                      tool_output.get("text") or \
                      tool_output.get("response") or \
                      "İşlem tamamlandı."
                return {"text": txt, "YANIT": txt, "ui_component": ui}

            # Metni hem 'data' içinden hem de ana çıktıdan ara
            data = tool_output.get("data") if "data" in tool_output else tool_output
            txt = (data.get("YANIT") if isinstance(data, dict) else None) or \
                  (data.get("text") if isinstance(data, dict) else None) or \
                  tool_output.get("YANIT") or \
                  tool_output.get("text") or \
                  tool_output.get("response")

            if txt:
                return {"text": txt, "YANIT": txt, "ui_component": ui}

            return {"text": "İşlem tamamlandı.", "YANIT": "İşlem tamamlandı.", "ui_component": ui}

        if isinstance(tool_output, str):
            return {"text": tool_output, "YANIT": tool_output, "ui_component": None}

        if hasattr(tool_output, "content"):
            txt = str(getattr(tool_output, "content"))
            return {"text": txt, "YANIT": txt, "ui_component": None}

        return {"text": "İşlem tamamlandı.", "YANIT": "İşlem tamamlandı.", "ui_component": None}

    # ---------- ReAct fallback ----------
    async def _react(self, text: str) -> Any:
        # Customer ID bilgisini system prompt'a ekle
        system_prompt_with_context = self.system_prompt
        if self.customer_id is not None:
            system_prompt_with_context += f"\n\nMüşteri ID: {self.customer_id} (otomatik olarak tool'lara eklenir)"
        
        msgs = [SystemMessage(content=system_prompt_with_context), HumanMessage(content=text)]
        try:
            resp = await self.agent.ainvoke({"messages": msgs})
            
            if resp and "messages" in resp and resp["messages"]:
                # Tool yanıtını bul (ToolMessage tipindeki mesajlarda)
                for i, msg in enumerate(resp["messages"]):
                    # ToolMessage tipindeki mesajlarda tool yanıtı var
                    if hasattr(msg, 'type') and msg.type == 'tool':
                        try:
                            tool_output = json.loads(msg.content)
                            if isinstance(tool_output, dict):
                                # LLM'in kendi karar vermesini sağla - manuel intent tespiti yok
                                return {"tool_output": tool_output, "intent": None}
                        except Exception as parse_error:
                            log.error(json.dumps({
                                "event": "tool_output_parse_error",
                                "error": str(parse_error),
                                "raw_output": msg.content
                            }))
                            pass
                
                # Tool yanıtı bulunamadıysa son mesajı kullan
                last = resp["messages"][-1]
                llm_content = getattr(last, "content", "") or getattr(last, "text", "") or "Yanıt üretilemedi."
                return llm_content
            return "Yanıt üretilemedi."
        except Exception as e:
            return {"error": f"react_error:{e}"}

# ------------- Singleton API -------------
_agent_singleton: Optional[BankingAgent] = None

async def get_agent() -> BankingAgent:
    global _agent_singleton
    if _agent_singleton is None:
        _agent_singleton = BankingAgent(MCP_URL)
        ok = await _agent_singleton.initialize()
        if not ok:
            raise RuntimeError("BankingAgent initialize failed")
    return _agent_singleton

async def agent_handle_message_async(user_text: str, *, customer_id: Optional[int], session_id: Optional[str]) -> Dict[str, Any]:
    agent = await get_agent()
    return await agent.run(user_text, customer_id=customer_id, session_id=session_id)
