# notificacoes/tts_webhook.py 🔊 CharlieCore Voice Ping v1.1

import requests
import os

# Webhook configurado via .env
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_TTS")

def enviar_mensagem_tts(texto: str):
    """
    Envia uma mensagem TTS (text-to-speech) simples para o Discord via webhook configurado.
    Útil para alertas rápidos com voz do Discord ativada.
    """
    if not WEBHOOK_URL:
        print("❌ Webhook TTS não configurado. Verifique a variável DISCORD_WEBHOOK_TTS no .env.")
        return

    payload = {
        "content": texto,
        "tts": True
    }

    try:
        response = requests.post(WEBHOOK_URL, json=payload)
        if response.status_code in [200, 204]:
            print("✅ Mensagem TTS enviada com sucesso ao Discord.")
        else:
            print(f"⚠️ Erro ao enviar TTS: HTTP {response.status_code} — {response.text}")
    except Exception as e:
        print(f"❌ Exceção ao enviar TTS: {e}")
