
import os,sys
if os.getenv('CHARLIE_TTS_MODE','auto').lower()=='mute' or os.getenv('ELEVENLABS_ENABLED','true').lower() in ('0','false','no'):
    print('📝 [MUTE] (legacy)')
    sys.exit(0)
import os, sys
try:
    from charlie_voice_safe import falar as _falar_safe
except Exception:
    def _falar_safe(texto, *a, **k): print(f"📝 [MUTE] {texto}")

# Early-exit: silenciar TTS no servidor
if os.getenv("CHARLIE_TTS_MODE","auto").lower()=="mute" or    os.getenv("ELEVENLABS_ENABLED","true").lower() in ("0","false","no"):
    # deduz texto básico a partir do argumento (manha|noite), ajuste se necessário
    _arg = (sys.argv[1] if len(sys.argv)>1 else "").lower()
    if "manha" in _arg:
        _texto = "Bom dia, comandante. Hoje é um novo dia para vencer. Vamos começar com foco total."
    elif "noite" in _arg:
        _texto = "Boa noite, comandante. CharlieCore finalizou as operações de hoje. Até breve."
    else:
        _texto = "Mensagem CharlieCore."
    _falar_safe(_texto)
    sys.exit(0)
from dotenv import load_dotenv
load_dotenv(override=True)

from charlie_voice_safe import falar
import sys

mensagem_tipo = sys.argv[1] if len(sys.argv) > 1 else "neutra"

mensagens = {
    "manha": "Bom dia, comandante. Hoje é um novo dia para vencer. Vamos começar com foco total.",
    "noite": "Boa noite, comandante. CharlieCore finalizou as operações de hoje. Até breve.",
    "motivacional": "Você é mais forte do que pensa. Avance com coragem, a vitória está logo à frente.",
    "alerta": "Atenção total. Um novo desafio se aproxima.",
    "urgente": "Situação crítica detectada. CharlieCore ativando o modo de resposta imediata.",
    "neutra": "CharlieCore pronta para operar. Comando reconhecido.",
}

emocao_por_tipo = {
    "manha": "alegre",
    "noite": "suave",
    "motivacional": "inspirador",
    "alerta": "urgente",
    "urgente": "urgente",
    "neutra": "neutra"
}

texto = mensagens.get(mensagem_tipo, mensagens["neutra"])
emocao = emocao_por_tipo.get(mensagem_tipo, "neutra")

falar(texto, emocao)
