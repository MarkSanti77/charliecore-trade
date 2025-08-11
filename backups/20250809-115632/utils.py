# utils.py — 🔍 Coleta real de dados e cálculo de indicadores para CharlieCore
import requests
import numpy as np
import pandas as pd
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.trend import MACD, EMAIndicator, ADXIndicator
from ta.volatility import BollingerBands, AverageTrueRange

def obter_dados(symbol, interval="5m", limit=150):
    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
        response = requests.get(url)
        response.raise_for_status()
        klines = response.json()
    except Exception as e:
        print(f"⚠️ Erro ao obter candles para {symbol} ({interval}): {e}")
        return None

    try:
        df = pd.DataFrame(klines, columns=[
            "timestamp", "open", "high", "low", "close", "volume",
            "close_time", "quote_asset_volume", "trades",
            "taker_base_vol", "taker_quote_vol", "ignore"
        ])
        df["close"] = df["close"].astype(float)
        df["high"] = df["high"].astype(float)
        df["low"] = df["low"].astype(float)
        df["volume"] = df["volume"].astype(float)

        # Indicadores
        rsi = RSIIndicator(close=df["close"]).rsi().iloc[-1]
        macd = MACD(close=df["close"])
        bb = BollingerBands(close=df["close"])
        stoch = StochasticOscillator(high=df["high"], low=df["low"], close=df["close"])
        ema_9 = EMAIndicator(close=df["close"], window=9).ema_indicator().iloc[-1]
        ema_21 = EMAIndicator(close=df["close"], window=21).ema_indicator().iloc[-1]
        ema_200 = EMAIndicator(close=df["close"], window=200).ema_indicator().iloc[-1] if len(df) >= 200 else df["close"].mean()
        atr = AverageTrueRange(high=df["high"], low=df["low"], close=df["close"]).average_true_range().iloc[-1]
        adx = ADXIndicator(high=df["high"], low=df["low"], close=df["close"]).adx().iloc[-1]
        obv = (df["volume"] * np.where(df["close"].diff() > 0, 1, -1)).cumsum().iloc[-1]

        # Supertrend mock (futuro: implementar)
        supertrend = 1 if df["close"].iloc[-1] > ema_21 else -1

        return {
            "price": df["close"].iloc[-1],
            "rsi": round(rsi, 2),
            "macd": round(macd.macd().iloc[-1], 4),
            "macd_signal": round(macd.macd_signal().iloc[-1], 4),
            "macd_hist": round(macd.macd_diff().iloc[-1], 4),
            "supertrend": supertrend,
            "obv": round(obv, 2),
            "stoch_k": round(stoch.stoch().iloc[-1], 2),
            "stoch_d": round(stoch.stoch_signal().iloc[-1], 2),
            "adx": round(adx, 2),
            "ema_9": round(ema_9, 2),
            "ema_21": round(ema_21, 2),
            "ema_200": round(ema_200, 2),
            "atr": round(atr, 2),
            "bb_high": round(bb.bollinger_hband().iloc[-1], 2),
            "bb_low": round(bb.bollinger_lband().iloc[-1], 2),
        }

    except Exception as e:
        print(f"⚠️ Erro ao calcular indicadores para {symbol}: {e}")
        return None
