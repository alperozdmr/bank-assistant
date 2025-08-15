# test.py
import asyncio

from fastmcp import Client


async def main():
    # MCP server'a bağlan
    async with Client("http://127.0.0.1:8081/sse") as client:
        # Mevcut tool listesini çek
        tools = await client.list_tools()

        print("🔧 Available tools:", tools)

        # reg=ToolRegistry()
        # print("Tools :" ,await reg.list_tools())

        # Dummy account_id ile get_balance çağır
        print("\n📡 Calling get_balance tool...")
        result = await client.call_tool("get_balance", {"account_id": 1})
        print("✅ Result:", result)


if __name__ == "__main__":
    asyncio.run(main())


# """
# # Kullanım:
# #   python test.py --list
# #   python test.py --call get_balance --kwargs "{""account_id"": 1}"   # PowerShell
# #   python test.py --call get_balance --account-id 1                   # kolay yol
# # """
# import json
# import argparse
# from registery import registry  # dosya adın 'registery.py' ise böyle bırak
# #
# def list_tools():
#      tools = registry.list_tools()
#      print("\n🧰 Kayıtlı tool'lar:")
#      print(json.dumps(tools, indent=2, ensure_ascii=False))
#
# def call_tool(name: str, kwargs_json: str, account_id: int | None):
#      func = registry.get_tool(name)
#      if not func:
#          print(f"❌ Tool bulunamadı: {name}")
#          return
#
#      if account_id is not None:
#          kwargs = {"account_id": account_id}
#      else:
#          try:
#              kwargs = json.loads(kwargs_json) if kwargs_json else {}
#          except json.JSONDecodeError as e:
#              print(f"❌ --kwargs JSON parse hatası: {e}")
#              print('💡 PowerShell örneği: --kwargs "{""account_id"": 1}"')
#              return
#
#      print(f"\n📡 Çağrılıyor: {name}  args={kwargs}")
#      try:
#          result = func(**kwargs)
#          print("✅ Sonuç:\n" + json.dumps(result, indent=2, ensure_ascii=False))
#      except TypeError as e:
#          print(f"❌ Parametre hatası: {e}")
#      except Exception as e:
#          print(f"❌ Çalışma sırasında hata: {e}")
#
# def main():
#      p = argparse.ArgumentParser(description="Registry test aracı")
#      p.add_argument("--list", action="store_true", help="Tool'ları listele")
#      p.add_argument("--call", type=str, help="Çağrılacak tool adı (örn: get_balance)")
#      p.add_argument("--kwargs", type=str, default="", help="Tool kwargs (JSON)")
#      p.add_argument("--account-id", type=int, default=None, help="get_balance için kısayol")
#      args = p.parse_args()
#
#      if args.list or (not args.call and not args.list):
#          list_tools()
#      if args.call:
#          call_tool(args.call, args.kwargs, args.account_id)
#
# if __name__ == "__main__":
#      main()
