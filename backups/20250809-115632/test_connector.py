from binance_connector import get_current_price, get_klines

print("📈 Preço atual BTC:", get_current_price())

klines = get_klines(interval="1h", limit=1)
print("🕒 Último candle 1h:", klines[0])
