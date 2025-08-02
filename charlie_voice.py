# charlie_voice.py 🎙️ CharlieCore Emotional Voice v4.1
import os
import requests
import uuid
import time
from voice_logger import log_fala  # ⬅️ Logger ativado

VOZ_PADRAO = "onyx"
WEBHOOK_AUDIO = os.getenv("DISCORD_AUDIO_WEBHOOK_URL")
PASTA_AUDIO = "audios"

EMOCOES = {
    "alegre": {"stability": 0.40, "similarity": 0.85},
    "triste": {"stability": 0.80, "similarity": 0.80},
    "neutra": {"stability": 0.65, "similarity": 0.75},
    "confiante": {"stability": 0.30, "similarity": 0.90},
    "preocupada": {"stability": 0.70, "similarity": 0.70},
    "tensa": {"stability": 0.90, "similarity": 0.65},
}

def falar(texto, emocao="neutra"):
    print(f"\n⚙️ Gerando fala com emoção: {emocao}")
    
    os.makedirs(PASTA_AUDIO, exist_ok=True)
    id_audio = str(uuid.uuid4())
    caminho_audio = os.path.join(PASTA_AUDIO, f"{id_audio}.mp3")
    url_api = f"https://api.elevenlabs.io/v1/text-to-speech/{VOZ_PADRAO}"

    payload = {
        "text": texto,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": EMOCOES.get(emocao, EMOCOES["neutra"])
    }

    headers = {
        "xi-api-key": os.getenv("ELEVENLABS_API_KEY"),
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url_api, json=payload, headers=headers)
        response.raise_for_status()

        with open(caminho_audio, "wb") as f:
            f.write(response.content)

        print("✅ Áudio gerado com sucesso.")

        if WEBHOOK_AUDIO:
            with open(caminho_audio, "rb") as f:
                file = {"file": (f"{id_audio}.mp3", f)}
                r = requests.post(WEBHOOK_AUDIO, files=file)
                if r.status_code == 200:
                    print("📡 Áudio enviado ao Discord com sucesso.")
                else:
                    print(f"⚠️ Falha ao enviar áudio ao Discord. Código: {r.status_code}")
        else:
            print("⚠️ WEBHOOK_AUDIO não configurado. Áudio salvo localmente.")

        # ✅ Log da fala
        log_fala(texto, emocao)

    except Exception as e:
        print(f"❌ Erro ao gerar ou enviar áudio: {e}")
        print("🎧 Emitindo fallback sonoro padrão...")
        fallback = os.path.join(PASTA_AUDIO, "falha.mp3")
        if os.path.exists(fallback):
            os.system(f"mpg123 {fallback}")
        else:
            print("⚠️ Nenhum fallback disponível.")
