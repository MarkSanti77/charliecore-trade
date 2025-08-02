import os
from binance.client import Client
from dotenv import load_dotenv

load_dotenv("config/keys.env")

api_key = os.getenv("BINANCE_API_KEY")
api_secret = os.getenv("BINANCE_API_SECRET")

client = Client(api_key, api_secret)

ticker = client.get_symbol_ticker(symbol="BTCUSDT")
print(f"📈 Preço atual do BTC: {ticker['price']}")
