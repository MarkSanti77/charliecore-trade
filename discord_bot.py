# discord_bot.py 📡 CharlieCore Tactical Discord Transmitter v3.1
import os
import requests
from dotenv import load_dotenv

load_dotenv()

WEBHOOK_GENERAL = os.getenv("DISCORD_WEBHOOK_URL")  # legado/geral
WEBHOOK_PREMIUM = os.getenv("DISCORD_WEBHOOK_PREMIUM", WEBHOOK_GENERAL)
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.75"))

def enviar_relatorio(texto: str):
    """
    Envia relatório longo para o Discord em blocos (formatação de code block).
    """
    if not WEBHOOK_GENERAL:
        print("❌ Webhook do Discord não configurado.")
        return

    partes = [texto[i:i+1900] for i in range(0, len(texto), 1900)]  # margem de segurança
    for idx, parte in enumerate(partes, 1):
        payload = {"content": f"```{parte}```"}
        try:
            r = requests.post(WEBHOOK_GENERAL, json=payload, timeout=10)
            r.raise_for_status()
            print(f"✅ Parte {idx}/{len(partes)} enviada.")
        except requests.exceptions.RequestException as e:
            print(f"❌ Erro ao enviar parte {idx}: {e}")

def enviar_alerta_entrada(mensagem: str, confidence_score: float = 0.0):
    """
    Envia alerta de entrada. Roteia para webhook premium se score >= threshold.
    """
    if not WEBHOOK_GENERAL:
        print("❌ Webhook do Discord não configurado.")
        return

    high_conf = confidence_score >= CONFIDENCE_THRESHOLD
    webhook = WEBHOOK_PREMIUM if high_conf else WEBHOOK_GENERAL
    prefixo = "🚀 **ENTRADA (HIGH CONF)**" if high_conf else "📣 **ENTRADA**"

    payload = {"content": f"{prefixo} (conf: {confidence_score:.2f})\n{mensagem}"}
    try:
        r = requests.post(webhook, json=payload, timeout=10)
        r.raise_for_status()
        print("✅ Alerta de entrada enviado.")
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro ao enviar alerta: {e}")
