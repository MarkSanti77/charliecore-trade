# discord_ttsbot.py 🌐 Envio de comandos de voz via TTS Bot no Discord
import requests

def enviar_mensagem_tts(texto, webhook_url):
    """
    Envia uma mensagem de texto com o comando /tts via webhook para ser lida pelo TTS Bot no Discord.
    
    Parâmetros:
    - texto: A frase que será lida no canal de voz.
    - webhook_url: URL do webhook do canal de texto onde o bot TTS está ativo.
    """
    print(f"🔄 Enviando mensagem para leitura automática no Discord...")

    payload = {
        "content": f"/tts {texto}"
    }

    try:
        response = requests.post(webhook_url, json=payload)
        if response.status_code == 204:
            print("📡 Comando TTS enviado com sucesso ao Discord.")
        else:
            print(f"⚠️ Falha ao enviar comando TTS. Código: {response.status_code}")
            print(f"📨 Detalhes: {response.text}")
    except Exception as e:
        print(f"❌ Erro ao enviar mensagem TTS: {e}")
