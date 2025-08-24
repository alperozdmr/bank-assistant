import json
import time
import urllib.request


def test_qwen_api():
    QWEN_ENDPOINT_URL = "https://api-qwen-31-load-predictor-tmp-automation-test-3.apps.datascience.prod2.deniz.denizbank.com/v1/chat/completions"
    MODEL_NAME = "default"

    # Konsoldan prompt al
    test_message = input("💬 Sorunuzu girin: ")

    headers = {"Content-Type": "application/json"}

    payload = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": test_message}],
        "chat_template_kwargs": {"enable_thinking": True},
        "temperature": 0.7,
        "top_p": 0.95,
        "max_tokens": 1024,
    }

    print("\n📡 API test is starting...\n")

    try:
        start_time = time.time()

        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            QWEN_ENDPOINT_URL, data=data, headers=headers, method="POST"
        )

        with urllib.request.urlopen(request) as response:
            end_time = time.time()
            elapsed_time = end_time - start_time

            status_code = response.getcode()
            response_body = response.read().decode("utf-8")

            if status_code == 200:
                result = json.loads(response_body)

                # Model cevabını çek
                if "choices" in result and len(result["choices"]) > 0:
                    answer = result["choices"][0]["message"]["content"]
                    print(f"✅ Model Yanıtı: {answer}")
                else:
                    print("⚠️ Modelden yanıt alınamadı.")

                print(f"\n⏱ Yanıt süresi: {elapsed_time:.2f} sn")
            else:
                print(f"❌ Bağlantı başarısız. Status code: {status_code}")
                print("Response Text:", response_body)

    except Exception as e:
        print("🚨 API çağrısı sırasında hata oluştu:", e)


if __name__ == "__main__":
    while True:
        test_qwen_api()
        print("\n" + "-" * 50 + "\n")
