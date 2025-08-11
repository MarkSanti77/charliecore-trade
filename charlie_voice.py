# charlie_voice.py 🎙️ CharlieCore v6.2 — Voz oficial com fallback local + envio ao Discord

import os
import requests
import pyttsx3
from dotenv import load_dotenv

load_dotenv()

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
DISCORD_WEBHOOK_TTS = os.getenv("DISCORD_WEBHOOK_TTS")
VOICE_ID = os.getenv("VOICE_ID", "x3mAOLD9WzlmrFCwA1S3")  # 🇧🇷 Voz ElevenLabs PT-BR padrão

def falar(texto, emocao="neutra"):
    print(f"\n🎙️ Fala requisitada: \"{texto}\"")
    print(f"⚙️ Emoção: {emocao} | Voice ID: {VOICE_ID}")
    print(f"🔐 ElevenLabs API: {'✅ OK' if ELEVENLABS_API_KEY else '❌ Faltando'}")
    print(f"📡 Webhook TTS: {'✅ OK' if DISCORD_WEBHOOK_TTS else '❌ Faltando'}")

    if ELEVENLABS_API_KEY:
        try:
            audio_path = gerar_audio_elevenlabs(texto)
            if audio_path:
                enviar_audio_para_discord(audio_path)
                return
        except Exception as e:
            print(f"❌ Erro na geração/envio ElevenLabs: {e}")

    print("🧩 Ativando fallback local com pyttsx3...")
    fallback_local(texto)

def gerar_audio_elevenlabs(texto):
    """
    Conecta com a API ElevenLabs para gerar o áudio com voz sintetizada.
    """
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    body = {
        "text": texto,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.4,
            "similarity_boost": 0.8
        }
    }

    response = requests.post(url, json=body, headers=headers)

    if response.status_code == 200:
        audio_path = "/tmp/charlie_voice.mp3"
        with open(audio_path, "wb") as f:
            f.write(response.content)
        print(f"✅ Áudio gerado: {audio_path}")
        return audio_path
    else:
        raise Exception(f"{response.status_code} {response.reason}: {response.text}")

def enviar_audio_para_discord(audio_path):
    """
    Envia o arquivo de áudio gerado para o canal configurado via webhook no Discord.
    """
    if not DISCORD_WEBHOOK_TTS:
        print("⚠️ Webhook do Discord para TTS não está configurado.")
        return

    print(f"📡 Enviando áudio para Discord...")

    try:
        with open(audio_path, "rb") as f:
            response = requests.post(
                DISCORD_WEBHOOK_TTS,
                files={"file": ("charlie_voice.mp3", f, "audio/mpeg")}
            )

        if response.status_code in [200, 204]:
            print("✅ Áudio enviado com sucesso ao Discord.")
        else:
            print(f"❌ Falha no envio. Código HTTP: {response.status_code} | {response.text}")
    except Exception as e:
        print(f"❌ Erro ao enviar áudio para Discord: {e}")

def fallback_local(texto):
    """
    Gera a fala localmente usando o mecanismo pyttsx3 (offline).
    """
    try:
        engine = pyttsx3.init()
        engine.setProperty("rate", 180)
        engine.setProperty("volume", 1.0)
        engine.say(texto)
        engine.runAndWait()
        print("✅ Fallback local executado com sucesso.")
    except Exception as e:
        print(f"⚠️ Erro no fallback local: {e}")
