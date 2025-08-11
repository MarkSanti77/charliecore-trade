# indicators/indicators.py 🔺 CharlieCore Tactical Indicators Engine vX.GoldPlus 🔱

import pandas as pd
import ta
from datetime import datetime
from data import get_klines, get_current_price

def convert_klines_to_dataframe(klines):
    df = pd.DataFrame(klines, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_asset_volume', 'number_of_trades',
        'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
    ])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    df = df.astype(float)
    return df

def calculate_supertrend(df, period=10, multiplier=3.0):
    hl2 = (df['high'] + df['low']) / 2
    atr = ta.volatility.AverageTrueRange(high=df['high'], low=df['low'], close=df['close'], window=period).average_true_range()
    upper_band = hl2 + multiplier * atr
    lower_band = hl2 - multiplier * atr
    trend = [1]
    supertrend = [hl2.iloc[0]]

    for i in range(1, len(df)):
        if df['close'][i] > upper_band[i - 1]:
            trend.append(1)
        elif df['close'][i] < lower_band[i - 1]:
            trend.append(-1)
        else:
            trend.append(trend[-1])

        if trend[-1] == 1:
            supertrend.append(max(lower_band[i], supertrend[-1]))
        else:
            supertrend.append(min(upper_band[i], supertrend[-1]))

    df['supertrend'] = supertrend
    return df

def analyze_indicators(symbol, interval):
    klines = get_klines(symbol, interval)
    if not klines:
        raise ValueError(f"❌ Nenhum dado de candle recebido para {symbol} {interval}")

    df = convert_klines_to_dataframe(klines)

    try:
        rsi = ta.momentum.RSIIndicator(close=df['close'], window=14).rsi().iloc[-1]
        obv = ta.volume.OnBalanceVolumeIndicator(close=df['close'], volume=df['volume']).on_balance_volume().iloc[-1]

        macd = ta.trend.MACD(close=df['close'])
        macd_line = macd.macd().iloc[-1]
        macd_signal = macd.macd_signal().iloc[-1]
        macd_hist = macd.macd_diff().iloc[-1]

        stoch = ta.momentum.StochasticOscillator(high=df['high'], low=df['low'], close=df['close'])
        stoch_k = stoch.stoch().iloc[-1]
        stoch_d = stoch.stoch_signal().iloc[-1]

        adx = ta.trend.ADXIndicator(high=df['high'], low=df['low'], close=df['close']).adx().iloc[-1]

        bb = ta.volatility.BollingerBands(close=df['close'])
        bb_high = bb.bollinger_hband().iloc[-1]
        bb_low = bb.bollinger_lband().iloc[-1]

        ema_9 = ta.trend.EMAIndicator(close=df['close'], window=9).ema_indicator().iloc[-1]
        ema_21 = ta.trend.EMAIndicator(close=df['close'], window=21).ema_indicator().iloc[-1]
        ema_200 = ta.trend.EMAIndicator(close=df['close'], window=200).ema_indicator().iloc[-1]

        atr = ta.volatility.AverageTrueRange(high=df['high'], low=df['low'], close=df['close']).average_true_range().iloc[-1]

        df = calculate_supertrend(df)
        supertrend_value = df['supertrend'].iloc[-1]
        current_price = df['close'].iloc[-1]
        supertrend = 1 if current_price > supertrend_value else -1

        timestamp = df.index[-1].strftime("%Y-%m-%d %H:%M:%S")

        return {
            "rsi": rsi,
            "obv": obv,
            "macd": macd_line,
            "macd_signal": macd_signal,
            "macd_hist": macd_hist,
            "stoch_k": stoch_k,
            "stoch_d": stoch_d,
            "adx": adx,
            "bb_high": bb_high,
            "bb_low": bb_low,
            "ema_9": ema_9,
            "ema_21": ema_21,
            "ema_200": ema_200,
            "atr": atr,
            "supertrend": supertrend,
            "price": current_price,
            "timestamp": timestamp
        }

    except Exception as e:
        print(f"❌ Erro ao calcular indicadores: {e}")
        return {}

def verificar_inicio_rsi(symbol):
    # 🔬 CharlieCore vX Sensor - Detecção futura de início de novo ciclo RSI
    return True
