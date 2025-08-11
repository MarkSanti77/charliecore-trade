# debug_env.py 🚀 Validador de Variáveis CharlieCore
from dotenv import load_dotenv
import os

load_dotenv()

webhook = os.getenv("DISCORD_AUDIO_WEBHOOK_URL")
api_key = os.getenv("ELEVENLABS_API_KEY")

print("🎯 DISCORD_AUDIO_WEBHOOK_URL:", webhook if webhook else "❌ Não encontrada")
print("🔑 ELEVENLABS_API_KEY:", api_key[:10] + "..." if api_key else "❌ Não encontrada")
