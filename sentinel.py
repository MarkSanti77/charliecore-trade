# sentinel.py 🚨 CharlieCore Sentinel + Emotional Voice Ops v5.0

import time
from indicators.indicators import analyze_indicators, verificar_inicio_rsi
from discord_bot import enviar_relatorio, enviar_alerta_entrada
from estrategia import avaliar_estrategia
from charlie_voice import falar

SYMBOLS = ["BTCUSDT", "ETHUSDT", "SUIUSDT", "XRPUSDT", "DOGEUSDT", "PEPEUSDT", "SOLUSDT"]
INTERVALS = ["15m", "1h", "4h"]
INTERVALO_SEGUNDOS = 900  # 15 minutos

def run_analysis():
    relatorio = []
    relatorio.append("=" * 60)
    relatorio.append("📡 CharlieCore Sentinel Report Iniciado")
    relatorio.append("=" * 60)

    falar("Iniciando varredura de ativos. Relatório tático em andamento.", emocao="neutra")

    for symbol in SYMBOLS:
        relatorio.append(f"\n🧠 Ativo Monitorado: {symbol}")
        if symbol != "BTCUSDT":
            relatorio.append("   🔄 Altcoin em foco: possível desacoplamento em análise.")

        for interval in INTERVALS:
            try:
                result = analyze_indicators(symbol, interval)
                decisao = avaliar_estrategia(result['rsi'], result['obv'], result['supertrend'], interval)

                linha = (
                    f"   ⏱ Intervalo: {interval} | "
                    f"RSI: {result['rsi']:.2f} | "
                    f"OBV: {result['obv']:.2f} | "
                    f"Trend: {'Alta ✅' if result['supertrend'] > 0 else 'Baixa ⚠️'}"
                )

                print(linha)
                relatorio.append(linha)
                relatorio.append(f"   💡 Estratégia sugerida: {decisao}")

                # ⚡ Alerta com voz confiante e envio pro Discord
                if ("entrada LONG" in decisao or "entrada SHORT" in decisao) and verificar_inicio_rsi(symbol):
                    mensagem_alerta = (
                        f"🎯 {symbol} | Intervalo: {interval} | "
                        f"Preço: {result['price']:.4f} | "
                        f"{decisao} | ⏱ {result['timestamp']}"
                    )
                    enviar_alerta_entrada(mensagem_alerta)
                    falar(f"Alerta de entrada autorizado para {symbol} no intervalo {interval}.", emocao="confiante")

            except Exception as e:
                erro = f"   ❌ Erro em {symbol} [{interval}]: {e}"
                print(erro)
                relatorio.append(erro)
                falar(f"Ocorreu um erro crítico ao analisar {symbol} em {interval}.", emocao="tensa")

    falar("Varredura finalizada. Aguardando o próximo ciclo.", emocao="neutra")
    relatorio.append("\n⚡ CharlieCore em alerta. Aguardando próximo comando.")
    return "\n".join(relatorio)

def main():
    while True:
        print("\n" + "=" * 50)
        print("🚨 CharlieCore Sentinel: Nova varredura iniciada")
        print("=" * 50)

        relatorio = run_analysis()
        enviar_relatorio(relatorio)

        print("⏳ Aguardando 15 minutos até a próxima varredura...")
        time.sleep(INTERVALO_SEGUNDOS)

if __name__ == "__main__":
    main()
