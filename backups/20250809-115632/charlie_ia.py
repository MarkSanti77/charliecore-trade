# charlie_ia.py 🤖 CharlieCore AI Module — Tactical Intelligence Interface
import os
import requests
from dotenv import load_dotenv

# === 🔰 FASE 1: BOOTSTRAP DO AMBIENTE === #
print("🧠 [CharlieCore] Iniciando carregamento de variáveis táticas...")
dotenv_ok = load_dotenv("config/keys.env")

if dotenv_ok:
    print("✅ [CharlieCore] Ambiente carregado com sucesso.")
else:
    print("⚠️ [CharlieCore] Falha ao carregar config/keys.env.")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    print("❌ [CharlieCore] Chave da OpenAI não encontrada no ambiente.")
else:
    print("🔐 [CharlieCore] Chave da OpenAI carregada.")

# === 🧠 FASE 2: FUNÇÃO DE RESPOSTA TÁTICA === #
def responder_mensagem(pergunta, modelo="gpt-3.5-turbo"):
    """
    Envia uma mensagem à OpenAI e retorna a resposta textual.
    Ideal para integração com Discord ou interfaces de comando.
    """
    if not OPENAI_API_KEY:
        return "❌ Chave da OpenAI não encontrada."

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": modelo,
        "messages": [
            {"role": "system", "content": "Você é Charlie, a IA tática da CharlieCore."},
            {"role": "user", "content": pergunta}
        ]
    }

    try:
        print("🚀 [CharlieCore] Enviando requisição à OpenAI...")
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=15
        )

        print(f"📡 [CharlieCore] Código de resposta: {response.status_code}")
        print("📝 [CharlieCore] Corpo da resposta:", response.text)

        if response.status_code == 200:
            resposta = response.json()["choices"][0]["message"]["content"]
            print("✅ [CharlieCore] Resposta recebida da IA.")
            return resposta.strip()
        else:
            return f"❌ Erro {response.status_code}: {response.text}"

    except Exception as e:
        print(f"🔥 [CharlieCore] Exceção durante requisição: {e}")
        return f"❌ Erro na requisição: {e}"
