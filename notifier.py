k# notifier.py 🚨 Sistema de Alerta CharlieCore v1.2

import requests
import os

# Recomendado: use variável de ambiente para segurança (fallback para o hardcoded se necessário)
DISCORD_WEBHOOK_URL = os.getenv(
    "CHARLIECORE_DISCORD_WEBHOOK",
    "https://discord.com/api/webhooks/1396935848498430002/PXpwl6uE7XfXUbZtxhlhpg9EDi9pzY4R5_JH2_DqVLZjds41aWlKxb4C8tOwWIHtzFTj"
)

def enviar_a_

