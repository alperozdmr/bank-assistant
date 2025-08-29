"""Langchain MCP Banking Agent Setup
vLLM compatible, Intelligent tool selection"""

import asyncio  
from datetime import datetime


try:
    
    from langchain_mcp_adapters.client import MultiServerMCPClient
    from langgraph.prebuilt import create_react_agent
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage ,SystemMessage
except ImportError as e:
    print("Eksik paketler var. Lütfen 'requirements.txt' dosyasını kontrol edin ve gerekli paketleri yükleyin.")


# === Configuration ===
MCP_URL = "http://127.0.0.1:8081/sse"
LLM_API_BASE = "https://router.huggingface.co/v1"
LLM_CHAT_PATH = "/chat/completions"
LLM_MODEL = "Qwen/Qwen3-30B-A3B:fireworks-ai"
LLM_API_KEY = "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"  # .env veya export HF_API_KEY=... ile

class BankingAgent:
    """Banking Agent using Langchain and MCP"""

    def __init__(self):
        self.agent = None
        self.client = None
        self.tools = []
        self.model = None
        self.system_prompt = """System prompt: You are a banking assistant. Use the tools to answer user queries about bank accounts and transactions.
        Rolün:Müşteri ihtiyaçlarına göre uygun banking tool 'ları seçerek profesyonel yanıtlar vermek.
        
        Kurallar:   
 """
    async def initialize(self):
            """Initialize Banking Agent"""
            try:
                print("Banking Agent başlatılıyor...")
                self.model =ChatOpenAI(
                    model_name=LLM_MODEL,
                    openai_api_base=LLM_API_BASE,
                    openai_api_key=LLM_API_KEY,
                    temperature=0.3,
                    max_completion_tokens=8192,
                    max_retries=3,
            
                    
                )
                print("LLM model hazır.")


                # MCP Client kurulumu

                print("MCP SERVER bağlantısı kuruluyor...")
                self.client = MultiServerMCPClient({
                    "fortuna_banking":{
                    "url": MCP_URL,
                    "transport": "sse"
                    }
                })

                ##Load "tools from MCP " ##toolara ulaştığımız yer
                print("MCP tools yükleniyor...")
                self.tools = await self.client.get_tools()
                print(f"{len(self.tools)} tools yüklendi.")


                for tool in self.tools:
                 print(f"Tool: {tool.name}") 

                # Agent oluşturma
                print("Agent oluşturuluyor...")
                self.agent = create_react_agent(  
                    model=self.model,     ##agenta beynini ve tool'ları veriyoruz!
                    tools=self.tools
                )
                print("Agent hazır.")

                return True
            
            except Exception as e:
                print(f"Agent başlatılırken hata oluştu: {e}")
                import traceback
                traceback.print_exc()
                return False
        

    async def run(self, user_message: str) -> str:

        """Smart banking chat with intelligent tool selection
        """
        try:
            print(f"Kullanıcı: {user_message}")
            print(f"Agent tool seçiyor...")

            messages= [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=user_message)

            ]
            #LangGraph agent Run
            response = await self.agent.ainvoke({
                "messages": messages
            })

            if response and "messages" in response:
                final_message = response["messages"][-1]
                return final_message.content
            else:
                return "Üzgünüm, bir hata oluştu veya geçersiz yanıt alındı."
            
        except Exception as e:
            print(f"Agent çalıştırılırken hata oluştu: {e}")
            import traceback
            traceback.print_exc()
            return "Üzgünüm, bir hata oluştu."
        
async def interact_banking_chat():
 
       print("Banking Agent ile etkileşim başlatılıyor...")
       print("Lütfen sorularınızı yazın (çıkmak için 'exit' yazın).")
       print("Örnek sorular:")
       print("- Hesap 3 bakiyesini söyler misin?")
       print("- Hesap 2 son 5 işlemini göster.")

       agent = BankingAgent()
       
       initialized = await agent.initialize()
       if not initialized:
        print("Agent başlatılamadı. Çıkılıyor...")
        return

       while True:
        user_input = input("Sen: ")
        if user_input.lower() == "exit":
            print("Görüşürüz!")
            break
        response = await agent.run(user_input)
        print(f"Agent: {response}")

if __name__ == "__main__":
    asyncio.run(interact_banking_chat())
    
           

                
