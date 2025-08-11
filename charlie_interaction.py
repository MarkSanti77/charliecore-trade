# charlie_interaction.py 🎙️ CharlieCore Discord Live Command v1.2
import os
import discord
import asyncio
from typing import Optional

from charlie_voice import falar
from scanner import analisar_ativo  # pipeline novo (snapshot → estratégia → score)
from discord_bot import enviar_alerta_entrada

CHANNEL_NAME = os.getenv("DISCORD_CHANNEL_NAME", "charliecore")

async def start_charlie_bot(client: discord.Client):
    await client.wait_until_ready()
    channel = discord.utils.get(client.get_all_channels(), name=CHANNEL_NAME)

    if channel:
        await channel.send("🛰️ CharlieCore online. Pronta para liderar. Comandante, suas ordens.")
        # ping leve periódico (mantém presença e lembra do comando)
        while not client.is_closed():
            await asyncio.sleep(3600)
            await channel.send("⏳ Deseja uma varredura? Envie `!analisar BTCUSDT` ou me mencione.")

async def on_message(message: discord.Message):
    # filtro de canal/bot
    if message.author.bot or message.channel.name != CHANNEL_NAME:
        return

    content = message.content.strip().lower()

    # detectar menção sem usar 'client' fora do escopo
    bot_me: Optional[discord.Member] = message.guild.me if message.guild else None
    bot_mencionada = any(m.id == bot_me.id for m in message.mentions) if bot_me else False

    if bot_mencionada:
        await message.channel.send("📡 Recebido, comandante. Estou ouvindo…")
        await falar("Comando recebido, comandante.", emocao="confiante")

    if content.startswith("!status"):
        await message.channel.send("✅ Todas as rotinas ativas. Pronta para sua próxima ordem, comandante.")
        await falar("Todas as rotinas estão ativas, comandante.", emocao="confiante")
        return

    if content.startswith("!help"):
        await message.channel.send(
            "**🧭 Comandos:**\n"
            "`!status` – Status do sistema\n"
            "`!analisar BTCUSDT` – Análise do ativo\n"
            "`@charlie` – Mencione para interagir\n"
        )
        return

    if content.startswith("!analisar"):
        try:
            parts = content.split()
            symbol = parts[1].upper() if len(parts) > 1 else os.getenv("SYMBOL", "BTCUSDT")

            # análise completa (snapshot → estratégia → ctx com score)
            msg, ctx = analisar_ativo(symbol)
            score = float(ctx.get("confidence_score", 0.0))
            direction = ctx.get("direction")  # definido no scanner (inferência textual)
            meets_threshold = bool(ctx.get("meets_threshold", False))

            # feedback no chat
            await message.channel.send(f"{msg}\n\n🎯 confidence_score: **{score:.2f}**")
            await falar(f"Análise de {symbol} concluída. Confiança {score:.2f}.", emocao="neutra")

            # disparo opcional de alerta por webhook (usa roteamento premium por score)
            if direction and meets_threshold:
                enviar_alerta_entrada(msg, confidence_score=score)

        except Exception as e:
            await message.channel.send(f"⚠️ Erro ao processar análise: `{e}`")
            await falar("Erro ao tentar analisar o ativo solicitado.", emocao="triste")
