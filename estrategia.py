# estrategia.py — CharlieCore Tactical Logic v5.1
# Compatível com a assinatura antiga (avaliar_estrategia) e com snapshot novo (avaliar_de_snapshot)

from __future__ import annotations
from typing import Optional, Dict, Any, Tuple, List

# =========================
# Utilidades internas
# =========================
def _valid(*args):
    return all(x is not None for x in args)

def _pct(a: float, b: float) -> int:
    if b == 0:
        return 0
    return round((a / b) * 100)

def _slope(values: List[Optional[float]], lookback: int = 10) -> Optional[float]:
    """Inclinação simples: diferença (último - n-ésimo) / n. Ignora None no fim."""
    seq = [v for v in values if v is not None]
    if len(seq) <= lookback:
        return None
    return (seq[-1] - seq[-1 - lookback]) / float(lookback)

def _last(values: List[Optional[float]]) -> Optional[float]:
    for x in reversed(values):
        if x is not None:
            return x
    return None

def _message_result(texto: str, meta: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    """Retorno padrão: (mensagem, contexto)"""
    return texto, meta

# =========================
# Núcleo: decisão por timeframe
# =========================
def _decisao_timeframe_maior(
    supertrend_dir: Optional[int],
    rsi: Optional[float],
    macd_hist: Optional[float],
    ema_fast: Optional[float],   # EMA curta (20)
    ema_slow: Optional[float],   # EMA longa (50)
    ema_trend: Optional[float] = None  # opcional (ex.: 200 se existir)
) -> Tuple[str, Dict[str, Any]]:
    """
    Interpretação para 4h/1h (tendência macro e intermediária).
    """
    if not _valid(supertrend_dir, rsi, macd_hist, ema_fast, ema_slow):
        return _message_result("⚠️ Dados insuficientes para avaliar tendência no timeframe maior.",
                               {"categoria": "insuficiente"})

    alta = (supertrend_dir or 0) > 0 and (rsi or 0) > 53 and (macd_hist or 0) > 0 and (ema_fast or 0) > (ema_slow or 0)
    baixa = (supertrend_dir or 0) < 0 and (rsi or 0) < 47 and (macd_hist or 0) < 0 and (ema_fast or 0) < (ema_slow or 0)

    # Se houver uma média de tendência (ex: 200), adiciona filtro
    if ema_trend is not None:
        if alta and (ema_slow or 0) > ema_trend:
            return _message_result("📈 Tendência de Alta ✅ — Força compradora alinhada (macro).",
                                   {"categoria": "tendencia_alta"})
        if baixa and (ema_slow or 0) < ema_trend:
            return _message_result("📉 Tendência de Baixa ✅ — Força vendedora alinhada (macro).",
                                   {"categoria": "tendencia_baixa"})

    if alta or baixa:
        return _message_result("🟡 Tendência intermediária — Acompanhar movimentação.",
                               {"categoria": "tendencia_intermediaria"})
    return _message_result("⚪ Zona neutra — Aguardando direcionamento.",
                           {"categoria": "neutra"})

def _score_tatico_5m(
    rsi: Optional[float],
    macd: Optional[float],
    macd_signal: Optional[float],
    macd_hist: Optional[float],
    supertrend_dir: Optional[int],
    ema_fast: Optional[float],  # 20
    ema_slow: Optional[float],  # 50
    obv_last: Optional[float],
    obv_series: Optional[List[Optional[float]]] = None,
    adx: Optional[float] = None,
) -> Tuple[str, Dict[str, Any]]:
    """
    Score tático para 5m. Pesos ajustados e OBV com inclinação recente.
    """
    score_long = 0
    score_short = 0
    total_peso = 0
    sinais_long: List[str] = []
    sinais_short: List[str] = []

    def add(cond: bool, peso: int, label: str, goes_long=True, goes_short=True):
        nonlocal score_long, score_short, total_peso
        total_peso += peso
        if cond:
            if goes_long:
                score_long += peso
                sinais_long.append(f"{label} ✅")
            if goes_short:
                score_short += peso
                sinais_short.append(f"{label} ✅")
        else:
            if goes_long:
                sinais_long.append(f"{label} ❌")
            if goes_short:
                sinais_short.append(f"{label} ❌")

    # RSI
    if rsi is not None:
        add(rsi > 50, 2, "RSI > 50", True, False)
        add(rsi < 50, 2, "RSI < 50", False, True)
    else:
        sinais_long.append("RSI ⚠️")
        sinais_short.append("RSI ⚠️")

    # MACD cruzamento
    if _valid(macd, macd_signal):
        add((macd or 0) > (macd_signal or 0), 2, "MACD cruzado ↑", True, False)
        add((macd or 0) < (macd_signal or 0), 2, "MACD cruzado ↓", False, True)
    else:
        sinais_long.append("MACD ⚠️")
        sinais_short.append("MACD ⚠️")

    # Histograma (momentum)
    if macd_hist is not None:
        add(macd_hist > 0, 1, "Hist ↑", True, False)
        add(macd_hist < 0, 1, "Hist ↓", False, True)
    else:
        sinais_long.append("Hist ⚠️")
        sinais_short.append("Hist ⚠️")

    # SuperTrend direção
    if supertrend_dir is not None:
        add(supertrend_dir > 0, 2, "SuperTrend ↑", True, False)
        add(supertrend_dir < 0, 2, "SuperTrend ↓", False, True)
    else:
        sinais_long.append("SuperTrend ⚠️")
        sinais_short.append("SuperTrend ⚠️")

    # EMAs 20/50
    if _valid(ema_fast, ema_slow):
        add((ema_fast or 0) > (ema_slow or 0), 2, "EMA20 > EMA50", True, False)
        add((ema_fast or 0) < (ema_slow or 0), 2, "EMA20 < EMA50", False, True)
    else:
        sinais_long.append("EMAs ⚠️")
        sinais_short.append("EMAs ⚠️")

    # OBV — usa inclinação recente (mais robusto que número absoluto)
    if obv_series and len([v for v in obv_series if v is not None]) > 15:
        obv_slope = _slope(obv_series, lookback=15)
        if obv_slope is not None:
            add(obv_slope > 0, 2, "OBV ↗", True, False)
            add(obv_slope < 0, 2, "OBV ↘", False, True)
        else:
            sinais_long.append("OBV slope ⚠️")
            sinais_short.append("OBV slope ⚠️")
    elif obv_last is not None:
        # fallback simples no último valor (menos confiável; mantido por compatibilidade)
        add(obv_last >= 0, 1, "OBV ≥ 0", True, False)
        add(obv_last < 0, 1, "OBV < 0", False, True)
    else:
        sinais_long.append("OBV ⚠️")
        sinais_short.append("OBV ⚠️")

    # ADX opcional
    if adx is not None:
        add(adx >= 17, 1, "ADX forte")
    else:
        sinais_long.append("ADX ⚠️")
        sinais_short.append("ADX ⚠️")

    if total_peso == 0:
        return _message_result("⛔ Nenhum dado disponível para pontuar o ativo.", {"categoria": "insuficiente"})

    pct_long = _pct(score_long, total_peso)
    pct_short = _pct(score_short, total_peso)

    if pct_long >= 65:
        return _message_result(
            f"🔥 ENTRADA DETECTADA\n📌 Estratégia: ✅ Entrada **LONG** — {pct_long}% de confluência.\n📊 Sinais: {', '.join(sinais_long)}",
            {"categoria": "long", "pct_long": pct_long, "pct_short": pct_short, "sinais": sinais_long}
        )
    if pct_short >= 65:
        return _message_result(
            f"🔥 ENTRADA DETECTADA\n📌 Estratégia: ⚠️ Entrada **SHORT** — {pct_short}% de confluência.\n📊 Sinais: {', '.join(sinais_short)}",
            {"categoria": "short", "pct_long": pct_long, "pct_short": pct_short, "sinais": sinais_short}
        )
    if pct_long >= 50:
        return _message_result(
            f"👀 POTENCIAL DE ENTRADA\n📌 Estratégia: 🟡 Possível **LONG** — {pct_long}% de confluência.\n📊 Sinais: {', '.join(sinais_long)}",
            {"categoria": "watch_long", "pct_long": pct_long, "pct_short": pct_short, "sinais": sinais_long}
        )
    if pct_short >= 50:
        return _message_result(
            f"👀 POTENCIAL DE ENTRADA\n📌 Estratégia: 🟠 Possível **SHORT** — {pct_short}% de confluência.\n📊 Sinais: {', '.join(sinais_short)}",
            {"categoria": "watch_short", "pct_long": pct_long, "pct_short": pct_short, "sinais": sinais_short}
        )

    return _message_result(
        f"⚪ SEM ENTRADA — LONG {pct_long}%, SHORT {pct_short}%.\n📊 Aguardando melhor cenário.",
        {"categoria": "no_trade", "pct_long": pct_long, "pct_short": pct_short}
    )

# =========================
# Função compatível (assinatura antiga)
# =========================
def avaliar_estrategia(
    rsi, obv, supertrend, interval,
    macd=None, macd_signal=None, macd_hist=None,
    stoch_k=None, stoch_d=None,
    adx=None, bb_high=None, bb_low=None,
    ema_9=None, ema_21=None, ema_200=None,
    atr=None, price=None
):
    """
    Mantida por compatibilidade. Internamente mapeia para:
    - Timeframes != 5m: avaliação de tendência (usando ema_21->fast, ema_200->slow quando possível)
    - 5m: score tático
    """
    # Mapear EMAs antigos para o novo modelo (fast/slow)
    ema_fast = ema_9 if ema_9 is not None else ema_21  # tentar a menor como fast
    ema_slow = ema_21 if ema_21 is not None else ema_200

    if interval != "5m":
        msg, meta = _decisao_timeframe_maior(
            supertrend_dir=supertrend,
            rsi=rsi,
            macd_hist=macd_hist,
            ema_fast=ema_fast,
            ema_slow=ema_slow,
            ema_trend=ema_200
        )
        return msg
    else:
        msg, meta = _score_tatico_5m(
            rsi=rsi,
            macd=macd,
            macd_signal=macd_signal,
            macd_hist=macd_hist,
            supertrend_dir=supertrend,
            ema_fast=ema_fast,
            ema_slow=ema_slow,
            obv_last=obv,
            obv_series=None,
            adx=adx
        )
        return msg

# =========================
# Nova API — trabalhar direto com snapshot do data.py
# =========================
def _extract_last(inds: Dict[str, Any]) -> Dict[str, Any]:
    """Extrai últimos valores úteis do dicionário de indicadores do data.py."""
    last = inds.get("last", {})
    return {
        "close": last.get("close"),
        "ema20": last.get("ema20"),
        "ema50": last.get("ema50"),
        "macd": last.get("macd"),
        "macd_signal": last.get("macd_signal"),
        "macd_hist": last.get("macd_hist"),
        "rsi14": last.get("rsi14"),
        "obv": last.get("obv"),
        "supertrend_dir": last.get("supertrend_dir"),
    }

def avaliar_de_snapshot(snapshot: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    """
    Usa o snapshot multi-timeframe do data.py para gerar decisão consolidada.
    Regras:
    - 4h: define a direção macro (preferência)
    - 1h: confirma a direção
    - 15m: confirma momento da entrada
    - 5m: score tático e timing
    Retorna (mensagem_discord, contexto_dict)
    """
    ctx: Dict[str, Any] = {"stages": {}}

    def get_inds(tf: str) -> Optional[Dict[str, Any]]:
        node = snapshot.get(tf)
        if not node or not node.get("ok"):
            return None
        return node.get("indicators")

    # 4h
    inds_4h = get_inds("4h")
    if inds_4h:
        last4h = _extract_last(inds_4h)
        msg4h, meta4h = _decisao_timeframe_maior(
            supertrend_dir=last4h["supertrend_dir"],
            rsi=last4h["rsi14"],
            macd_hist=last4h["macd_hist"],
            ema_fast=last4h["ema20"],
            ema_slow=last4h["ema50"],
            ema_trend=None  # se quiser inserir EMA200 no futuro
        )
        ctx["stages"]["4h"] = {"msg": msg4h, **meta4h}
    else:
        ctx["stages"]["4h"] = {"msg": "4h indisponível", "categoria": "insuficiente"}

    # 1h
    inds_1h = get_inds("1h")
    if inds_1h:
        last1h = _extract_last(inds_1h)
        msg1h, meta1h = _decisao_timeframe_maior(
            supertrend_dir=last1h["supertrend_dir"],
            rsi=last1h["rsi14"],
            macd_hist=last1h["macd_hist"],
            ema_fast=last1h["ema20"],
            ema_slow=last1h["ema50"],
            ema_trend=None
        )
        ctx["stages"]["1h"] = {"msg": msg1h, **meta1h}
    else:
        ctx["stages"]["1h"] = {"msg": "1h indisponível", "categoria": "insuficiente"}

    # 15m (confirmação de entrada)
    inds_15m = get_inds("15m")
    if inds_15m:
        last15 = _extract_last(inds_15m)
        msg15, meta15 = _decisao_timeframe_maior(
            supertrend_dir=last15["supertrend_dir"],
            rsi=last15["rsi14"],
            macd_hist=last15["macd_hist"],
            ema_fast=last15["ema20"],
            ema_slow=last15["ema50"],
            ema_trend=None
        )
        ctx["stages"]["15m"] = {"msg": msg15, **meta15}
    else:
        ctx["stages"]["15m"] = {"msg": "15m indisponível", "categoria": "insuficiente"}

    # 5m (tático)
    inds_5m = get_inds("5m")
    if inds_5m:
        last5 = _extract_last(inds_5m)
        msg5, meta5 = _score_tatico_5m(
            rsi=last5["rsi14"],
            macd=last5["macd"],
            macd_signal=last5["macd_signal"],
            macd_hist=last5["macd_hist"],
            supertrend_dir=last5["supertrend_dir"],
            ema_fast=last5["ema20"],
            ema_slow=last5["ema50"],
            obv_last=last5["obv"],
            obv_series=inds_5m.get("obv"),  # série completa se quiser usar slope
            adx=None
        )
        ctx["stages"]["5m"] = {"msg": msg5, **meta5}
    else:
        ctx["stages"]["5m"] = {"msg": "5m indisponível", "categoria": "insuficiente"}

    # Consolidação simples (exemplo):
    cat4h = ctx["stages"]["4h"].get("categoria")
    cat1h = ctx["stages"]["1h"].get("categoria")
    cat15 = ctx["stages"]["15m"].get("categoria")
    cat5 = ctx["stages"]["5m"].get("categoria")

    # Heurística: precisa de alinhamento 4h/1h; 15m não neutro; 5m indica timing
    if cat4h == "tendencia_alta" and cat1h in {"tendencia_alta", "tendencia_intermediaria"}:
        if cat15 in {"tendencia_alta", "tendencia_intermediaria"}:
            if cat5 in {"long", "watch_long"}:
                msg_final = "✅ **Entrada LONG autorizada** — Macro e timing alinhados."
            else:
                msg_final = "🟡 **Segurar mão** — Tendência de alta, aguardando 5m confirmar."
        else:
            msg_final = "⚪ **Alta macro** — 15m neutro. Aguardando melhora no curto."
    elif cat4h == "tendencia_baixa" and cat1h in {"tendencia_baixa", "tendencia_intermediaria"}:
        if cat15 in {"tendencia_baixa", "tendencia_intermediaria"}:
            if cat5 in {"short", "watch_short"}:
                msg_final = "⚠️ **Entrada SHORT autorizada** — Macro e timing alinhados."
            else:
                msg_final = "🟠 **Segurar mão** — Tendência de baixa, aguardando 5m confirmar."
        else:
            msg_final = "⚪ **Baixa macro** — 15m neutro. Aguardando melhora no curto."
    else:
        msg_final = "🚫 **Não entrar agora** — Timeframes desalinhados."

    # --- Lift de métricas do 5m para o topo ---
    m5 = ctx["stages"].get("5m", {}) if isinstance(ctx.get("stages"), dict) else {}
    if m5:
        if "pct_long" in m5: ctx["pct_long"] = m5["pct_long"]
        if "pct_short" in m5: ctx["pct_short"] = m5["pct_short"]
        if "confidence_score" not in ctx:
            try:
                ctx["confidence_score"] = max(int(m5.get("pct_long", 0)), int(m5.get("pct_short", 0))) / 100.0
            except Exception:
                ctx["confidence_score"] = 0.0

    # Direção inferida pelo texto final (compat)
    txt_final = (msg_final or "").lower()
    if "entrada long autorizada" in txt_final or "entrada **long**" in txt_final:
        ctx["direction"] = "LONG"
    elif "entrada short autorizada" in txt_final or "entrada **short**" in txt_final:
        ctx["direction"] = "SHORT"

    return _message_result(msg_final, ctx)
