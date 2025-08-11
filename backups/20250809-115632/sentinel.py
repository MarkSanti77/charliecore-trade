# sentinel.py 🚨 CharlieCore Sentinel v1.6
# Módulo de monitoramento contínuo com sistema de alerta para entradas táticas

import asyncio
from scanner import analisar_ativos
from notifier import enviar_alerta_discord

INTERVALOS = ["15m", "1h", "4h", "5m"]
ATIVOS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "PEPEUSDT", "DOGEUSDT"]
PAUSA_ENTRE_RODADAS = 300  # 5 minutos

async def sentinela():
    while True:
        total_calls = 0
        log_rodada = ["📡 Iniciando nova varredura tática...\n"]

        for simbolo in ATIVOS:
            log_rodada.append(f"🧐 Ativo Monitorado: {simbolo}")
            ativo_teve_call = False

            for intervalo in INTERVALOS:
                resultado = await analisar_ativos(simbolo, intervalo)

                if resultado is None:
                    log_rodada.append(f"   ⚠️ Dados insuficientes para {simbolo} em {intervalo}.")
                    continue

                if isinstance(resultado, dict) and resultado.get("mensagem"):
                    entrada_formatada = (
                        f"🔥 ENTRADA DETECTADA\n"
                        f"📌 Ativo: {resultado['ativo']}\n"
                        f"⏱️ Tempo Gráfico: {resultado['intervalo']}\n"
                        f"🎯 Estratégia: {resultado['mensagem']}"
                    )
                    await enviar_alerta_discord(entrada_formatada)
                    total_calls += 1
                    ativo_teve_call = True
                else:
                    log_rodada.append(f"   🔍 Analisando {simbolo} em {intervalo}...\n   {resultado}")

            if not ativo_teve_call:
                log_rodada.append("   💤 Nenhuma entrada detectada neste ativo.")

        log_rodada.append(f"\n📊 Total de calls detectadas nesta rodada: {total_calls}")

        # Só envia o log geral se houver pelo menos 1 call
        if total_calls > 0:
            await enviar_alerta_discord("\n".join(log_rodada))
        else:
            print("\n".join(log_rodada))  # Apenas imprime localmente

        await asyncio.sleep(PAUSA_ENTRE_RODADAS)

if __name__ == "__main__":
    try:
        asyncio.run(sentinela())
    except KeyboardInterrupt:
        print("🛑 Execução interrompida manualmente.")
