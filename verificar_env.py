# verificar_env.py 🧪 Diagnóstico de variáveis .env

import os
from dotenv import load_dotenv

load_dotenv()

print("🎯 DISCORD_WEBHOOK_TTS:", os.getenv("DISCORD_WEBHOOK_TTS") or "❌ NÃO DEFINIDO")
print("🎯 ELEVENLABS_API_KEY:", (os.getenv("ELEVENLABS_API_KEY")[:8] + "...") if os.getenv("ELEVENLABS_API_KEY") else "❌ NÃO DEFINIDO")
print("🎯 VOICE_ID:", os.getenv("VOICE_ID") or "❌ NÃO DEFINIDO")
