# data.py — Coleta + Indicadores + Snapshot (CharlieCore blindado)
from __future__ import annotations
import os, time
from typing import Any, Dict, List, Optional, Tuple
import requests

# ========= Config (.env) =========
BINANCE_BASE   = os.getenv("BINANCE_BASE", "https://api.binance.com")
USER_AGENT     = os.getenv("HTTP_USER_AGENT", "CharlieCore/5.0 (+https://github.com/charliecore)")
SNAPSHOT_LIMIT = int(os.getenv("SNAPSHOT_LIMIT", "500"))
MIN_BARS       = int(os.getenv("MIN_BARS", "80"))
ST_PERIOD      = int(os.getenv("ST_PERIOD", "10"))
ST_MULT        = float(os.getenv("ST_MULT", "3.0"))

# ========= Infra de rede (retry/backoff + 429) =========
def _request_json(path: str, params: Dict[str, Any]) -> Any:
    url = f"{BINANCE_BASE}{path}"
    tries = 4
    backoff = 0.9
    for i in range(tries):
        try:
            r = requests.get(url, params=params, timeout=8, headers={"User-Agent": USER_AGENT})
            if r.status_code == 429:  # rate limit
                wait = int(r.headers.get("Retry-After", 1)) or 1
                time.sleep(wait if i == tries - 1 else (wait + backoff * (i + 1)))
                if i == tries - 1:
                    r.raise_for_status()
                continue
            r.raise_for_status()
            return r.json()
        except Exception as e:
            if i == tries - 1:
                print(f"❌ Erro de rede em {path} {params}: {e}")
                raise
            time.sleep(backoff * (i + 1))

# ========= Coleta =========
def get_current_price(symbol: str = "BTCUSDT") -> Optional[float]:
    try:
        data = _request_json("/api/v3/ticker/price", {"symbol": symbol})
        return float(data["price"])
    except Exception as e:
        print(f"❌ Erro ao obter preço atual [{symbol}]: {e}")
        return None

def get_klines_raw(symbol: str = "BTCUSDT", interval: str = "15m", limit: int = SNAPSHOT_LIMIT) -> Optional[List[list]]:
    try:
        limit = max(50, min(int(limit), 1000))  # clamp 50–1000
        return _request_json("/api/v3/klines", {"symbol": symbol, "interval": interval, "limit": limit})
    except Exception as e:
        print(f"❌ Erro ao obter candles [{symbol} {interval}]: {e}")
        return None

def get_klines(symbol: str = "BTCUSDT", interval: str = "15m", limit: int = SNAPSHOT_LIMIT) -> Optional[List[Dict[str, float]]]:
    """
    Retorna candles parseados (floats):
    open_time, open, high, low, close, volume, close_time
    """
    raw = get_klines_raw(symbol, interval, limit)
    if not raw:
        return None
    if len(raw) < MIN_BARS:
        print(f"⚠️ Apenas {len(raw)} candles no timeframe {interval}, mínimo exigido: {MIN_BARS}")
        return None
    out: List[Dict[str, float]] = []
    for k in raw:
        out.append({
            "open_time": float(k[0]),
            "open": float(k[1]),
            "high": float(k[2]),
            "low": float(k[3]),
            "close": float(k[4]),
            "volume": float(k[5]),
            "close_time": float(k[6]),
        })
    return out

# ========= Indicadores (implementações puras) =========
def ema(values: List[float], period: int) -> List[Optional[float]]:
    if period <= 0: raise ValueError("period must be > 0")
    if not values: return []
    k = 2 / (period + 1)
    out: List[Optional[float]] = [None] * len(values)
    if len(values) >= period:
        seed = sum(values[:period]) / period
        out[period - 1] = seed
        for i in range(period, len(values)):
            out[i] = values[i] * k + out[i - 1] * (1 - k)  # type: ignore
    return out

def macd(values: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[List[Optional[float]], List[Optional[float]], List[Optional[float]]]:
    ema_fast = ema(values, fast)
    ema_slow = ema(values, slow)
    macd_line: List[Optional[float]] = [None] * len(values)
    for i in range(len(values)):
        if ema_fast[i] is not None and ema_slow[i] is not None:
            macd_line[i] = ema_fast[i] - ema_slow[i]  # type: ignore
    signal_line = ema([x if x is not None else 0.0 for x in macd_line], signal)
    hist: List[Optional[float]] = [None] * len(values)
    for i in range(len(values)):
        if macd_line[i] is not None and signal_line[i] is not None:
            hist[i] = macd_line[i] - signal_line[i]  # type: ignore
    return macd_line, signal_line, hist

def rsi(values: List[float], period: int = 14) -> List[Optional[float]]:
    if not values: return []
    out: List[Optional[float]] = [None] * len(values)
    gains: List[float] = [0.0] * len(values)
    losses: List[float] = [0.0] * len(values)
    for i in range(1, len(values)):
        diff = values[i] - values[i - 1]
        gains[i] = max(diff, 0.0)
        losses[i] = max(-diff, 0.0)
    avg_gain = ema(gains[1:], period)
    avg_loss = ema(losses[1:], period)
    avg_gain = [None] + avg_gain
    avg_loss = [None] + avg_loss
    for i in range(len(values)):
        if i == 0 or avg_gain[i] is None or avg_loss[i] is None:
            out[i] = None; continue
        if avg_loss[i] == 0:
            out[i] = 100.0
        else:
            rs = (avg_gain[i] or 0.0) / (avg_loss[i] or 1e-12)
            out[i] = 100.0 - (100.0 / (1.0 + rs))
    return out

def obv(closes: List[float], volumes: List[float]) -> List[Optional[float]]:
    if not closes or not volumes or len(closes) != len(volumes): return []
    out: List[Optional[float]] = [None] * len(closes)
    total = 0.0
    out[0] = 0.0
    for i in range(1, len(closes)):
        if closes[i] > closes[i - 1]: total += volumes[i]
        elif closes[i] < closes[i - 1]: total -= volumes[i]
        out[i] = total
    return out

def supertrend(high: List[float], low: List[float], close: List[float], period: int = ST_PERIOD, multiplier: float = ST_MULT) -> Tuple[List[Optional[float]], List[Optional[int]]]:
    if not (len(high) == len(low) == len(close)):
        raise ValueError("Listas de high/low/close devem ter o mesmo tamanho.")
    n = len(close)
    if n == 0: return [], []
    tr: List[float] = [0.0] * n
    for i in range(n):
        if i == 0:
            tr[i] = high[i] - low[i]
        else:
            tr[i] = max(high[i] - low[i], abs(high[i] - close[i - 1]), abs(low[i] - close[i - 1]))
    atr: List[Optional[float]] = [None] * n
    if n >= period:
        for i in range(period - 1, n):
            atr[i] = sum(tr[i - period + 1: i + 1]) / period
    basic_ub: List[Optional[float]] = [None] * n
    basic_lb: List[Optional[float]] = [None] * n
    for i in range(n):
        if atr[i] is not None:
            hl2 = (high[i] + low[i]) / 2.0
            basic_ub[i] = hl2 + multiplier * atr[i]
            basic_lb[i] = hl2 - multiplier * atr[i]
    final_ub: List[Optional[float]] = [None] * n
    final_lb: List[Optional[float]] = [None] * n
    for i in range(n):
        if i == 0:
            final_ub[i] = basic_ub[i]; final_lb[i] = basic_lb[i]
        else:
            final_ub[i] = (basic_ub[i] if (basic_ub[i] is not None and (final_ub[i-1] is None or basic_ub[i] < final_ub[i-1] or close[i-1] > final_ub[i-1])) else final_ub[i-1])
            final_lb[i] = (basic_lb[i] if (basic_lb[i] is not None and (final_lb[i-1] is None or basic_lb[i] > final_lb[i-1] or close[i-1] < final_lb[i-1])) else final_lb[i-1])
    st: List[Optional[float]] = [None] * n
    dir_: List[Optional[int]] = [None] * n
    for i in range(n):
        if i == 0 or final_ub[i] is None or final_lb[i] is None:
            st[i] = None; dir_[i] = None; continue
        prev_st = st[i-1]; prev_dir = dir_[i-1]
        if prev_st is None or prev_dir is None:
            if close[i] > final_ub[i]: st[i] = final_lb[i]; dir_[i] = 1
            elif close[i] < final_lb[i]: st[i] = final_ub[i]; dir_[i] = -1
            else: st[i] = final_lb[i]; dir_[i] = 1
        elif prev_dir == 1:
            st[i] = final_lb[i] if close[i] <= prev_st else max(final_lb[i], prev_st)
            dir_[i] = -1 if close[i] <= prev_st else 1
        else:
            st[i] = final_ub[i] if close[i] >= prev_st else min(final_ub[i], prev_st)
            dir_[i] = 1 if close[i] >= prev_st else -1
    return st, dir_

# ========= Agregador de indicadores =========
def compute_indicators(klines: List[Dict[str, float]]) -> Dict[str, Any]:
    closes  = [k["close"]  for k in klines]
    highs   = [k["high"]   for k in klines]
    lows    = [k["low"]    for k in klines]
    volumes = [k["volume"] for k in klines]

    ema20 = ema(closes, 20)
    ema50 = ema(closes, 50)
    macd_line, signal_line, hist = macd(closes)
    rsi14 = rsi(closes, 14)
    obv_line = obv(closes, volumes)
    st_line, st_dir = supertrend(highs, lows, closes, period=ST_PERIOD, multiplier=ST_MULT)

    def last_valid(arr: List[Optional[float | int]]) -> Optional[float | int]:
        for x in reversed(arr):
            if x is not None:
                return x
        return None

    return {
        "ema20": ema20,
        "ema50": ema50,
        "macd": macd_line,
        "macd_signal": signal_line,
        "macd_hist": hist,
        "rsi14": rsi14,
        "obv": obv_line,
        "supertrend": st_line,
        "supertrend_dir": st_dir,
        "last": {
            "close": closes[-1] if closes else None,
            "ema20": last_valid(ema20),
            "ema50": last_valid(ema50),
            "macd": last_valid(macd_line),
            "macd_signal": last_valid(signal_line),
            "macd_hist": last_valid(hist),
            "rsi14": last_valid(rsi14),
            "obv": last_valid(obv_line),
            "supertrend_dir": last_valid(st_dir),
        },
    }

# ========= Snapshot multi-timeframe =========
def get_market_snapshot(
    symbol: str = "BTCUSDT",
    intervals: List[str] = ("4h", "1h", "15m", "5m"),
    limit: int = SNAPSHOT_LIMIT,
) -> Dict[str, Any]:
    """Retorna {interval: {klines, indicators, ok}} por timeframe."""
    out: Dict[str, Any] = {}
    for itv in intervals:
        ks = get_klines(symbol, itv, limit)
        if not ks or len(ks) < MIN_BARS:
            out[itv] = {"klines": ks or [], "indicators": None, "ok": False}
            continue
        inds = compute_indicators(ks)
        out[itv] = {"klines": ks, "indicators": inds, "ok": True}
    return out
