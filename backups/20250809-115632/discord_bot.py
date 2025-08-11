# discord_bot.py 📡 CharlieCore Tactical Discord Transmitter v3.0 (Resiliente)

import os
import requests
from dotenv import load_dotenv

load_dotenv()

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

def enviar_relatorio(texto):
    """
    Envia o relatório completo para o Discord, dividindo em blocos menores se ultrapassar 2000 caracteres.
    """
    if not WEBHOOK_URL:
        print("❌ Webhook do Discord não configurado.")
        return

    partes = [texto[i:i+1900] for i in range(0, len(texto), 1900)]  # margem de segurança

    for idx, parte in enumerate(partes):
        payload = {
            "content": f"```{parte}```"
        }

        try:
            response = requests.post(WEBHOOK_URL, json=payload, timeout=10)
            response.raise_for_status()
            print(f"✅ Parte {idx + 1}/{len(partes)} enviada com sucesso.")
        except requests.exceptions.Timeout:
            print(f"⏳ Timeout ao enviar parte {idx + 1}/{len(partes)}.")
        except requests.exceptions.RequestException as e:
            print(f"❌ Erro ao enviar parte {idx + 1}/{len(partes)} para Discord: {e}")
        except requests.exceptions.RequestException as e:
            print(f"❌ Erro ao enviar parte {idx + 1} para Discord: {e}")
        except Exception as e:
            print(f"❌ Erro inesperado ao enviar parte {idx + 1}: {e}")

def enviar_alerta_entrada(mensagem):
    """
    Envia um alerta tático individual ao Discord para entradas confirmadas (LONG ou SHORT).
    """
    if not WEBHOOK_URL:
        print("❌ Webhook do Discord não configurado.")
        return

    alerta_payload = {
        "content": f"🚀 **ENTRADA AUTORIZADA**\n{mensagem}"
    }

    try:
        response = requests.post(WEBHOOK_URL, json=alerta_payload, timeout=10)
        response.raise_for_status()
        print("✅ Alerta de entrada enviado com sucesso.")
    except requests.exceptions.Timeout:
        print("⏳ Timeout ao enviar alerta para o Discord.")
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro ao enviar alerta de entrada para Discord: {e}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro ao enviar alerta para Discord: {e}")
    except Exception as e:
        print(f"❌ Erro inesperado ao enviar alerta: {e}")

