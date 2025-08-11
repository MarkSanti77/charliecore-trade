# scanner.py — Varredura tática (context-aware direction)
from __future__ import annotations
import os
from typing import Tuple, Dict, Any, Optional, List
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"), override=True)

from data import get_market_snapshot
from estrategia import avaliar_de_snapshot  # fluxo novo (snapshot → estratégia)

# -------------------------------------------------------------
SNAPSHOT_LIMIT: int = int(os.getenv("SNAPSHOT_LIMIT", "500"))
DEFAULT_INTERVALS: List[str] = ["4h", "1h", "15m", "5m"]
CONFIDENCE_THRESHOLD: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.75"))
# -------------------------------------------------------------


def _infer_direction_from_msg(msg: str) -> Optional[str]:
    t = msg.lower()
    if "entrada long autorizada" in t or "entrada **long**" in t:
        return "LONG"
    if "entrada short autorizada" in t or "entrada **short**" in t:
        return "SHORT"
    return None


def _infer_direction_from_ctx(ctx: Dict[str, Any]) -> Optional[str]:
    """Fallback: usa alinhamento macro + 5m para derivar direção."""
    stages = ctx.get("stages", {})
    cat4h = (stages.get("4h") or {}).get("categoria")
    cat1h = (stages.get("1h") or {}).get("categoria")
    cat15 = (stages.get("15m") or {}).get("categoria")
    cat5  = (stages.get("5m") or {}).get("categoria")

    long_macro_ok  = (cat4h == "tendencia_alta"  and cat1h in {"tendencia_alta", "tendencia_intermediaria"})
    short_macro_ok = (cat4h == "tendencia_baixa" and cat1h in {"tendencia_baixa", "tendencia_intermediaria"})

    # se 15m não contradiz (neutro ou alinhado), aceitar timing do 5m
    long_ok  = long_macro_ok  and cat15 in { "tendencia_alta", "tendencia_intermediaria", "neutra" }
    short_ok = short_macro_ok and cat15 in { "tendencia_baixa", "tendencia_intermediaria", "neutra" }

    if long_ok and cat5 in {"long", "watch_long"}:
        return "LONG"
    if short_ok and cat5 in {"short", "watch_short"}:
        return "SHORT"
    return None


def analisar_ativo(symbol: Optional[str] = None,
                   intervals: Optional[List[str]] = None) -> Tuple[str, Dict[str, Any]]:
    """
    Executa análise consolidada usando snapshot multi-timeframe.
    Retorna (mensagem_formatada, contexto_dict) prontos para o Discord.
    """
    symbol = (symbol or os.getenv("SYMBOL", "BTCUSDT")).upper()
    intervals = intervals or DEFAULT_INTERVALS

    try:
        snap = get_market_snapshot(symbol, intervals, limit=SNAPSHOT_LIMIT)
        msg, ctx = avaliar_de_snapshot(snap)
    except Exception as e:
        msg = f"⚠️ Erro ao analisar {symbol}: {e}"
        ctx = {"symbol": symbol, "error": str(e), "confidence_score": 0.0}

    # enriquecer contexto
    ctx["symbol"] = symbol

    # garantir confidence_score (fallback via pct_long/short se presente)
    if "confidence_score" not in ctx:
        long_pct = ctx.get("pct_long", 0)
        short_pct = ctx.get("pct_short", 0)
        ctx["confidence_score"] = max(long_pct, short_pct) / 100.0

    # direção por texto OU por contexto (fallback)
    direction = _infer_direction_from_msg(msg)
    if direction is None:
        direction = _infer_direction_from_ctx(ctx)

    ctx["direction"] = direction
    ctx["meets_threshold"] = float(ctx.get("confidence_score", 0.0)) >= CONFIDENCE_THRESHOLD
    ctx["authorized"] = bool(direction) and ctx["meets_threshold"]

    return msg, ctx


# ===== Compat fluxo antigo (async) =====
async def analisar_ativos(simbolo: Optional[str] = None, intervalo: str = "5m"):
    if simbolo is None:
        return None

    msg, ctx = analisar_ativo(simbolo)

    print(f"\n🧐 Ativo Monitorado: {simbolo} | Intervalo: {intervalo}")
    print(f"   {msg}")

    direction = ctx.get("direction")
    if direction:
        return {
            "ativo": simbolo,
            "intervalo": intervalo,
            "mensagem": msg,
            "direcao": direction,
            "confidence_score": ctx.get("confidence_score", 0.0),
            "meets_threshold": ctx.get("meets_threshold", False),
            "authorized": ctx.get("authorized", False),
            "contexto": ctx
        }
    return None

# --- API p/ CharlieCore Auto ---

# === CharlieCore: get_candidates (real) ===
import os, math, statistics
from typing import List, Dict, Any
from data import get_market_snapshot, get_klines, ema, obv

def _ema_pair(closes, fast=5, slow=10):
    efast = ema(closes, fast); eslow = ema(closes, slow)
    return efast, eslow

def _trend_bias(closes, fast=5, slow=10):
    efast, eslow = _ema_pair(closes, fast, slow)
    a = efast[-1]; b = eslow[-1]
    if a is None or b is None: return "flat"
    return "up" if a>b else ("down" if a<b else "flat")

def _obv_dir(closes, volumes, bars=3):
    o = obv(closes, volumes)
    last = [x for x in o if x is not None][-bars:]
    if len(last)<bars: return "flat"
    inc = all(last[i] <= last[i+1] for i in range(len(last)-1))
    dec = all(last[i] >= last[i+1] for i in range(len(last)-1))
    return "up" if inc and not dec else ("down" if dec and not inc else "flat")

def _vol_expanding(closes, win=20):
    if len(closes) < win*3: return "flat"
    now = statistics.pstdev(closes[-win:])
    prev= statistics.pstdev(closes[-2*win:-win])
    return "expanding" if (now > prev*1.05 and now>0) else ("contracting" if now < prev*0.95 else "flat")

def _atr_from_klines(ks, period=5):
    if len(ks) < period+1: return None
    trs=[]
    for i in range(1,len(ks)):
        h=ks[i]["high"]; l=ks[i]["low"]; cprev=ks[i-1]["close"]
        trs.append(max(h-l, abs(h-cprev), abs(l-cprev)))
    if len(trs)<period: return None
    return sum(trs[-period:])/period

def _corr_abs(a, b):
    n = min(len(a), len(b))
    if n<10: return 0.0
    a=a[-n:]; b=b[-n:]
    ma=sum(a)/n; mb=sum(b)/n
    va=sum((x-ma)**2 for x in a); vb=sum((y-mb)**2 for y in b)
    if va==0 or vb==0: return 0.0
    cov=sum((a[i]-ma)*(b[i]-mb) for i in range(n))
    return abs(cov / math.sqrt(va*vb))

def _returns(closes):
    out=[]
    for i in range(1,len(closes)):
        out.append(0.0 if closes[i-1]==0 else (closes[i]/closes[i-1]-1.0))
    return out

def get_candidates() -> List[Dict[str,Any]]:
    assets = os.getenv("ASSETS","BTCUSDT,ETHUSDT").split(",")
    assets = [a.strip().upper() for a in assets if a.strip()]
    limit  = int(os.getenv("SNAPSHOT_LIMIT","500"))
    out=[]
    # pré-carrega BTC 15m p/ acoplamento
    btc15 = get_klines("BTCUSDT","15m", min(limit,500)) or []
    btc_cl = [k["close"] for k in btc15] if btc15 and isinstance(btc15[0],dict) else ([k[4] for k in btc15] if btc15 else [])
    for sym in assets:
        snap = get_market_snapshot(sym, intervals=["1h","15m","5m"], limit=limit)
        if not all(snap.get(tf,{}).get("ok") for tf in ["1h","15m","5m"]):
            continue

        k15 = snap["15m"]["klines"]; k1h = snap["1h"]["klines"]; k5m = snap["5m"]["klines"]
        c15 = [k["close"] for k in k15]; c1h = [k["close"] for k in k1h]; c5m = [k["close"] for k in k5m]
        v15 = [k["volume"] for k in k15]

        b15 = _trend_bias(c15,5,10); b1h = _trend_bias(c1h,5,10)
        od  = _obv_dir(c15, v15, bars=3)
        vol = _vol_expanding(c15, win=20)

        atr5 = _atr_from_klines(k5m, period=5) or 1e-6
        e10  = ema(c15,10)[-1] or c15[-1]
        prox = abs(c15[-1]-e10)/atr5

        if sym != "BTCUSDT" and btc_cl:
            coup = _corr_abs(_returns(c15), _returns(btc_cl))
        else:
            coup = 1.0

        if b15=="up" and b1h=="up":
            out.append({"symbol":sym,"side":"long",
                        "confs":f"1h/15m ↑, OBV↑, vol {vol}, BTC acoplado {coup:.2f}",
                        "timing":"A (pullback-rejeição)","coupling":coup,
                        "trend_ok":True,"obv_ok":(od=='up'),"bollinger":vol,
                        "atr_proximity":prox,"invalidations":False})
        if b15=="down" and b1h=="down":
            out.append({"symbol":sym,"side":"short",
                        "confs":f"1h/15m ↓, OBV↓, vol {vol}, BTC acoplado {coup:.2f}",
                        "timing":"B (linha dos 50)","coupling":coup,
                        "trend_ok":True,"obv_ok":(od=='down'),"bollinger":vol,
                        "atr_proximity":prox,"invalidations":False})
    return out

"""
    Retorna lista de candidatos de trade.
    Cada item é um dict com no mínimo:
    symbol, side ('long'|'short'), confs, timing, coupling (0-1),
    trend_ok (bool), obv_ok (bool), bollinger ('expanding'|'flat'|'contracting'),
    atr_proximity (float; ex.: 0.42 == 0,42 x ATR5m), invalidations (bool)
    """
    candidates = []

    # TODO: Preencher com sua lógica real de varredura.
    # Exemplo (remova depois):
    # candidates.append({
    #   "symbol": "PEPEUSDT", "side": "short",
    #   "confs": "15m/1h ↓, OBV↓, Bollinger abrindo, BTC acoplado 0.82",
    #   "timing": "B (linha dos 50)",
    #   "coupling": 0.82,
    #   "trend_ok": True, "obv_ok": True, "bollinger": "expanding",
    #   "atr_proximity": 0.40,
    #   "invalidations": False
    # })
    return candidates
