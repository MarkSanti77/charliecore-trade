# executor.py 🎯 CharlieCore Order Executor
import os
from binance.client import Client
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")

client = Client(API_KEY, API_SECRET)
client.FUTURES_URL = 'https://fapi.binance.com/fapi'  # Testnet: 'https://testnet.binancefuture.com'

def enviar_ordem(symbol, lado, quantidade=0.01):
    """
    Envia ordem de mercado (LONG ou SHORT)
    lado: "BUY" para LONG, "SELL" para SHORT
    """
    try:
        ordem = client.futures_create_order(
            symbol=symbol,
            side=lado,
            type='MARKET',
            quantity=quantidade
        )
        print(f"🚀 Ordem enviada: {ordem['side']} {ordem['origQty']} {ordem['symbol']}")
        return ordem
    except Exception as e:
        print(f"❌ Erro ao enviar ordem: {e}")
        return None
