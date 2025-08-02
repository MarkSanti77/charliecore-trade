import pandas as pd
import numpy as np
from .supertrend import Supertrend
from ta.momentum import RSIIndicator
from ta.volume import OnBalanceVolumeIndicator
from data import get_klines, get_current_price


def analyze_indicators(symbol, interval):
    klines = get_klines(symbol=symbol, interval=interval, limit=200)
    if not klines or len(klines) < 50:
        raise ValueError("Não há candles suficientes para análise.")

    df = pd.DataFrame(klines, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_asset_volume', 'number_of_trades',
        'taker_buy_base_volume', 'taker_buy_quote_volume', 'ignore'
    ])
    df['close'] = pd.to_numeric(df['close'])
    df['high'] = pd.to_numeric(df['high'])
    df['low'] = pd.to_numeric(df['low'])
    df['volume'] = pd.to_numeric(df['volume'])

    rsi = RSIIndicator(close=df['close'], window=14).rsi().iloc[-1]
    obv = OnBalanceVolumeIndicator(close=df['close'], volume=df['volume']).on_balance_volume().iloc[-1]

    supertrend = Supertrend(
        high=df['high'],
        low=df['low'],
        close=df['close'],
        window=10,
        multiplier=3.0
    ).supertrend_direction().iloc[-1]

    timestamp = pd.to_datetime(df['timestamp'].iloc[-1], unit='ms')

    return {
        'rsi': rsi,
        'obv': obv,
        'supertrend': supertrend,
        'price': df['close'].iloc[-1],
        'timestamp': timestamp.strftime("%Y-%m-%d %H:%M:%S")
    }


def verificar_inicio_rsi(symbol, candles=10):
    """
    Verifica se o RSI está fazendo curva ascendente nos últimos candles de 5m.
    Ideal para confirmar início de movimento técnico.
    """
    klines = get_klines(symbol=symbol, interval="5m", limit=candles + 14)
    if not klines or len(klines) < candles + 14:
        raise ValueError("Não há dados suficientes para análise do RSI 5m.")

    df = pd.DataFrame(klines, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_asset_volume', 'number_of_trades',
        'taker_buy_base_volume', 'taker_buy_quote_volume', 'ignore'
    ])
    df['close'] = pd.to_numeric(df['close'])

    rsi_series = RSIIndicator(close=df['close'], window=14).rsi()
    ultimos_rsi = rsi_series.tail(candles)

    tendencia_ascendente = all(x < y for x, y in zip(ultimos_rsi, ultimos_rsi[1:]))

    return tendencia_ascendente
