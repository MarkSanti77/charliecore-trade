# discord_bot.py 📡 CharlieCore Tactical Discord Transmitter
import os
import requests

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

def enviar_relatorio(texto):
    """
    Envia o relatório dividido em partes menores se exceder o limite do Discord (2000 caracteres).
    """
    if not WEBHOOK_URL:
        print("❌ Webhook do Discord não configurado.")
        return

    partes = [texto[i:i+1900] for i in range(0, len(texto), 1900)]

    for idx, parte in enumerate(partes):
        payload = {
            "content": f"```{parte}```"
        }

        try:
            response = requests.post(WEBHOOK_URL, json=payload)
            if response.status_code == 204:
                print(f"✅ Parte {idx+1}/{len(partes)} enviada com sucesso ao Discord.")
            else:
                print(f"⚠️ Falha ao enviar parte {idx+1}. Código: {response.status_code}")
        except Exception as e:
            print(f"❌ Erro ao enviar parte {idx+1} para Discord: {e}")

def enviar_alerta_entrada(mensagem):
    """
    Envia uma mensagem de entrada tática separada no Discord (LONG/SHORT autorizada).
    """
    if not WEBHOOK_URL:
        print("❌ Webhook do Discord não configurado.")
        return

    alerta_payload = {
        "content": f"🚀 **ENTRADA AUTORIZADA**\n{mensagem}"
    }

    try:
        response = requests.post(WEBHOOK_URL, json=alerta_payload)
        if response.status_code == 204:
            print("✅ Entrada autorizada enviada ao Discord.")
        else:
            print(f"⚠️ Falha ao enviar entrada. Código: {response.status_code}")
    except Exception as e:
        print(f"❌ Erro ao enviar entrada para Discord: {e}")
