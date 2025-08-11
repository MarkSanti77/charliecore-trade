from dotenv import load_dotenv; load_dotenv(override=True)
import os, sys
try:
    from charlie_voice_safe import falar as falar_safe
except Exception:
    def falar_safe(texto, *a, **k): print(f"📝 [MUTE] {texto}")

arg = (sys.argv[1] if len(sys.argv)>1 else "").lower()
if "manha" in arg:
    texto = "Bom dia, comandante. Hoje é um novo dia para vencer. Vamos começar com foco total."
elif "noite" in arg:
    texto = "Boa noite, comandante. CharlieCore finalizou as operações de hoje. Até breve."
else:
    texto = "Mensagem CharlieCore."

# Modo silencioso no VPS (sem ElevenLabs/pyttsx3)
if os.getenv("CHARLIE_TTS_MODE","auto").lower() == "mute" or \
   os.getenv("ELEVENLABS_ENABLED","true").lower() in ("0","false","no"):
    print(f"📝 [MUTE] {texto}")
    sys.exit(0)

# Se algum dia quiser voz, o wrapper encaminha
falar_safe(texto)
