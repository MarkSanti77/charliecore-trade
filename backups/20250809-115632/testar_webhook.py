import os
import requests
from dotenv import load_dotenv

load_dotenv()

webhook_url = os.getenv("DISCORD_WEBHOOK_TTS")

if not webhook_url:
    print("❌ Webhook não configurado. Verifique a variável DISCORD_WEBHOOK_TTS.")
    exit(1)

mensagem = "CharlieCore online, pronta para servir com máxima eficiência, comandante."

payload = {
    "content": mensagem,
    "tts": True
}

response = requests.post(webhook_url, json=payload)

if response.status_code == 204:
    print("✅ Mensagem TTS enviada com sucesso para o Discord.")
else:
    print(f"❌ Falha ao enviar mensagem. Status code: {response.status_code}")
    print("Resposta:", response.text)
