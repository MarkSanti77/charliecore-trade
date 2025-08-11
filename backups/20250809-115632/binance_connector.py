# binance_connector.py 🌐 CharlieCore Data Pipeline v2.0
import os
from binance.client import Client
from dotenv import load_dotenv

load_dotenv(dotenv_path='config/keys.env')

api_key = os.getenv("BINANCE_API_KEY")
api_secret = os.getenv("BINANCE_API_SECRET")

client = Client(api_key, api_secret)

def get_current_price(symbol="BTCUSDT"):
    try:
        ticker = client.get_symbol_ticker(symbol=symbol)
        return float(ticker["price"])
    except Exception as e:
        print(f"❌ Erro ao obter preço atual de {symbol}: {e}")
        return None

def get_klines(symbol="BTCUSDT", interval="15m", limit=100):
    try:
        candles = client.get_klines(symbol=symbol, interval=interval, limit=limit)
        if not candles:
            raise ValueError("⚠️ Nenhum candle retornado da Binance.")
        return candles
    except Exception as e:
        print(f"❌ Erro ao obter candles [{symbol} - {interval}]: {e}")
        return []
