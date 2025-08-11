# notifier.py — Envio de alertas para o Discord
import requests
import os

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL") or "https://discord.com/api/webhooks/1396935848498430002/PXpwl6uE7XfXUbZtxhlhpg9EDi9pzY4R5_JH2_DqVLZjds41aWlKxb4C8tOwWIHtzFTj"

def enviar_alerta_discord(mensagem):
    payload = {
        "content": mensagem,
        "username": "CharlieCore 📡"
    }

    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        response.raise_for_status()
        print("✅ Alerta enviado com sucesso!")
        return True
    except Exception as e:
        print(f"❌ Erro ao enviar alerta: {e}")
        return False
