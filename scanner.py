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
def get_candidates():
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
