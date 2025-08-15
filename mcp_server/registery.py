# # registry.py
# from typing import Dict, Any
# from fastmcp import FastMCP
# import server  # Import your existing server module
#
# class ToolRegistry: # Scans the server and maintains an internal dictionary of the registered tools
#     def __init__(self):
#         self._tools: Dict[str, Any] = {}
#         self._collect_tools()
#
#     def _collect_tools(self):
#         """Collect all tools registered in server.py"""
#         # Get the MCP instance from server.py
#         self.mcp = server.mcp
#
#         # Register tools by inspecting the server module
#         self._tools["get_balance"] = {
#             "function": server.get_balance,
#             "description": server.get_balance.__doc__,
#             "signature": dict(server.get_balance.__annotations__)
#         }
#
#     def list_tools(self) -> Dict[str, Any]:
#         """List all registered tools with metadata"""
#         return {
#             name: {
#                 "description": tool["description"].strip(),
#                 "signature": tool["signature"]
#             }
#             for name, tool in self._tools.items()
#         }
#
#     def get_tool(self, tool_name: str):
#         """Get a tool function by name"""
#         return self._tools.get(tool_name, {}).get("function")
#
# # Singleton instance
# registry = ToolRegistry()

import inspect
from typing import Any, Callable, Dict, get_type_hints

import server  # server.py: mcp, get_balance (FunctionTool), account_tools vb.


class ToolRegistry:
    """
    server.py'deki @mcp.tool() sarmalayıcılarını tespit eder,
    alttaki gerçek fonksiyonu (impl) çıkarır ve çağrılabilir bir proxy döndürür.
    """

    def __init__(self):
        self._tools: Dict[str, Dict[str, Any]] = {}
        self.mcp = getattr(server, "mcp", None)
        self._collect_tools()

    # ---------- yardımcılar ----------

    def _unwrap_callable(self, obj: Any) -> Callable | None:
        """
        FunctionTool gibi sarmalayıcılardan alttaki gerçek fonksiyonu bul.
        Sırasıyla .__wrapped__, .fn, .function, .func, .impl denenir.
        """
        if callable(obj):
            return obj
        for attr in ("__wrapped__", "fn", "function", "func", "impl"):
            inner = getattr(obj, attr, None)
            if inner and callable(inner):
                return inner
        return None

    def _make_invoker(self, target: Callable) -> Callable:
        """kwargs ile çağırılabilir proxy; test.py burayı kullanır."""

        def _invoke(**kwargs):
            return target(**kwargs)

        return _invoke

    def _meta_from_callable(
        self, call_proxy: Callable, meta_source: Callable
    ) -> Dict[str, Any]:
        description = inspect.getdoc(meta_source) or ""
        hints = get_type_hints(meta_source)
        signature = {
            name: (t.__name__ if hasattr(t, "__name__") else str(t))
            for name, t in hints.items()
        }
        try:
            sig = inspect.signature(meta_source)
            params = [p.name for p in sig.parameters.values() if p.name != "self"]
        except (TypeError, ValueError):
            params = []
        return {
            "function": call_proxy,  # çağrılacak proxy
            "description": description,
            "signature": signature,
            "parameters": params,
        }

    # ---------- toplama ----------

    def _collect_tools(self):
        # 1) server.get_balance -> FunctionTool olabilir
        wrapper = getattr(server, "get_balance", None)
        impl = None

        if wrapper is not None:
            impl = self._unwrap_callable(wrapper)

        # 2) Hâlâ bulunamadıysa sınıf metodundan (account_tools.get_balance) al
        if impl is None:
            account_tools = getattr(server, "account_tools", None)
            if account_tools is not None:
                candidate = getattr(account_tools, "get_balance", None)
                if candidate:
                    impl = self._unwrap_callable(candidate)

        # 3) Kayıt
        if impl is not None:
            invoker = self._make_invoker(impl)
            self._tools["get_balance"] = self._meta_from_callable(invoker, impl)
        elif wrapper is not None:
            # En kötü senaryo: wrapper'ı çağrılamaz ama metadata verir
            invoker = self._make_invoker(
                wrapper
            )  # burada çağrı TypeError verir ama listeleme çalışır
            self._tools["get_balance"] = self._meta_from_callable(invoker, wrapper)

    # ---------- API ----------

    def list_tools(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        for name, meta in self._tools.items():
            out[name] = {
                "description": (meta.get("description") or "").strip(),
                "signature": meta.get("signature", {}),
                "parameters": meta.get("parameters", []),
            }
        return out

    def get_tool(self, tool_name: str):
        meta = self._tools.get(tool_name)
        return meta["function"] if meta else None

    def call(self, tool_name: str, **kwargs):
        fn = self.get_tool(tool_name)
        if not fn:
            raise KeyError(f"Tool not found: {tool_name}")
        return fn(**kwargs)


# Singleton
registry = ToolRegistry()
