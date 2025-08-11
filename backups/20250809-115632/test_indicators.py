# test_indicators.py 🚀
import pandas as pd
from indicators import analyze_indicators
from binance_connector import get_klines

def main():
    symbol = "BTCUSDT"
    interval = "15m"

    print(f"🧠 Analisando {symbol} no intervalo {interval}...")

    klines = get_klines(symbol=symbol, interval=interval)
    if not klines:
        print("❌ Falha ao obter os candles.")
        return

    df = pd.DataFrame(klines, columns=[
        "timestamp", "open", "high", "low", "close", "volume",
        "close_time", "quote_asset_volume", "number_of_trades",
        "taker_buy_base_volume", "taker_buy_quote_volume", "ignore"
    ])

    df[["open", "high", "low", "close", "volume"]] = df[["open", "high", "low", "close", "volume"]].astype(float)

    result = analyze_indicators(symbol, interval)
    print("✅ Resultado da análise:")
    print(result)

if __name__ == "__main__":
    main()
