# main.py 🚀 CharlieCore Discord Main Entrypoint

import discord
import asyncio
from charlie_interaction import start_charlie_bot, on_message

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"🤖 CharlieCore conectada como {client.user}")
    await start_charlie_bot(client)

# Evento de mensagens
client.event(on_message)

# Token (pegue do .env ou insira diretamente – segurança total recomendada via .env)
import os
DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
client.run(DISCORD_TOKEN)
