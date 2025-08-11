# voice_logger.py 📒 CharlieCore Voice Logger v2.1
import os
from datetime import datetime
import glob

PASTA_LOGS = "logs/falas"

def log_fala(texto, emocao="neutra"):
    try:
        hoje = datetime.now().strftime("%Y-%m-%d")
        pasta_emocao = os.path.join(PASTA_LOGS, emocao, hoje)
        os.makedirs(pasta_emocao, exist_ok=True)

        timestamp = datetime.now().strftime("%H-%M-%S")
        nome_arquivo = f"{timestamp}.txt"
        caminho_arquivo = os.path.join(pasta_emocao, nome_arquivo)

        with open(caminho_arquivo, "w", encoding="utf-8") as f:
            f.write(f"[{datetime.now()}] Emoção: {emocao}\n")
            f.write(f"Texto:\n{texto}\n")

        print(f"📝 Fala registrada em: {caminho_arquivo}")
    except Exception as e:
        print(f"⚠️ Erro ao registrar fala: {e}")

def replay_voz(emocao="neutra", data=None):
    if data is None:
        data = datetime.now().strftime("%Y-%m-%d")

    caminho = os.path.join(PASTA_LOGS, emocao, data)
    if not os.path.exists(caminho):
        print(f"⚠️ Nenhuma fala encontrada para '{emocao}' em {data}")
        return

    arquivos = sorted(glob.glob(os.path.join(caminho, "*.mp3")))
    if not arquivos:
        print(f"📁 Arquivos .mp3 não encontrados em {caminho}")
        return

    print(f"🔁 Reproduzindo {len(arquivos)} fala(s) de {emocao} em {data}")
    for audio in arquivos:
        print(f"🎧 {audio}")
        os.system(f"mpg123 '{audio}'")
