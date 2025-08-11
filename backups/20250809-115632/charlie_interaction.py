# charlie_interaction.py 🎙️ CharlieCore Discord Live Command v1.0

import discord
import asyncio
from charlie_voice import falar
from indicators.indicators import analyze_indicators
from estrategia import avaliar_estrategia

CHANNEL_NAME = "charliecore"

async def start_charlie_bot(client):
    await client.wait_until_ready()
    channel = discord.utils.get(client.get_all_channels(), name=CHANNEL_NAME)

    if channel:
        await channel.send("🛰️ CharlieCore online. Pronta para liderar. Comandante, suas ordens.")
        while not client.is_closed():
            await asyncio.sleep(3600)
            await channel.send("⏳ Comandante, deseja uma nova varredura? Envie `!analisar BTCUSDT` ou me mencione.")

async def on_message(message):
    if message.author.bot or message.channel.name != CHANNEL_NAME:
        return

    content = message.content.lower()
    mention = client.user.mention.lower()

    if mention in content:
        await message.channel.send("📡 Recebido, comandante. Estou ouvindo...")
        await falar("Comando recebido, comandante.", emocao="confiante")

    if content.startswith("!status"):
        await message.channel.send("✅ Todas as rotinas ativas. Pronta para sua próxima ordem, comandante.")
        await falar("Todas as rotinas estão ativas, comandante.", emocao="confiante")

    elif content.startswith("!analisar"):
        try:
            symbol = content.split()[1].upper()
            interval = "15m"
            result = analyze_indicators(symbol, interval)
            estrategia = avaliar_estrategia(
                rsi=result['rsi'],
                obv=result['obv'],
                supertrend=result['supertrend'],
                intervalo=interval
            )

            msg = (
                f"📊 Análise de {symbol} | Intervalo: {interval}\n"
                f"RSI: {result['rsi']:.2f}, OBV: {result['obv']:.2f}, Supertrend: {'Alta' if result['supertrend'] > 0 else 'Baixa'}\n"
                f"💡 Estratégia sugerida: {estrategia}"
            )
            await message.channel.send(msg)
            await falar(f"Análise de {symbol} concluída. {estrategia}", emocao="neutra")
        except Exception as e:
            await message.channel.send(f"⚠️ Erro ao processar análise: {e}")
            await falar("Erro ao tentar analisar o ativo solicitado.", emocao="triste")

    elif content.startswith("!help"):
        await message.channel.send(
            "**🧭 CharlieCore Comandos Disponíveis:**\n"
            "`!status` – Status do sistema\n"
            "`!analisar BTCUSDT` – Análise do ativo\n"
            "`@charlie` – Mencione para interagir\n"
        )
