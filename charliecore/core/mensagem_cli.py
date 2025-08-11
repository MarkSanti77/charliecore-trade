#!/usr/bin/env python3
import os, sys
from dotenv import load_dotenv
load_dotenv(override=True)

arg = (sys.argv[1] if len(sys.argv) > 1 else "").lower()
if "manha" in arg:
    texto = "Bom dia, comandante. Hoje é um novo dia para vencer. Vamos começar com foco total."
elif "noite" in arg:
    texto = "Boa noite, comandante. CharlieCore finalizou as operações de hoje. Até breve."
else:
    texto = "Mensagem CharlieCore."

# Checagem ANTES de qualquer import que fale
tts_mode = os.getenv("CHARLIE_TTS_MODE", "auto").lower()
eleven_on = os.getenv("ELEVENLABS_ENABLED", "true").lower() not in ("0","false","no")

if tts_mode == "mute" or not eleven_on:
    print(f"📝 [MUTE] {texto}")
    sys.exit(0)

# Caminho sonoro: usa wrapper seguro e deixa o charlie_mensagem fazer o resto
from charlie_voice_safe import falar as falar_safe
falar_safe(texto)
sys.exit(0)
