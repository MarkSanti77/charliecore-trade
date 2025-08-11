# sentinel.py — CharlieCore Sentinel v6.4 (Discord + Backend + TP/SL + cooldown)
import os, json, time, random, signal, asyncio
from datetime import datetime
from typing import Tuple, Dict, Any, Optional, List

import requests
from dotenv import load_dotenv

from scanner import analisar_ativo
from discord_bot import enviar_alerta_entrada, enviar_relatorio
from data import get_current_price

# ===== Env =====
BASE_DIR = os.path.dirname(__file__)
load_dotenv(dotenv_path=os.path.join(BASE_DIR, ".env"), override=True)

ASSETS: List[str] = [s.strip().upper() for s in os.getenv(
    "ASSETS",
    "BTCUSDT,ETHUSDT,SOLUSDT,PEPEUSDT,DOGEUSDT,BNBUSDT,LINKUSDT,ADAUSDT,MATICUSDT,AVAXUSDT"
).split(",") if s.strip()]

CONCURRENCY: int = int(os.getenv("MAX_CONCURRENCY", os.getenv("CONCURRENCY", "3")))
INTERVAL: int = int(os.getenv("INTERVAL_SECONDS", "900"))
MESSAGE_COOLDOWN: int = int(os.getenv("MESSAGE_COOLDOWN_SECONDS", "300"))
STATE_PATH: str = os.getenv("CHARLIE_STATE_PATH", os.path.expanduser("~/.charlie_state.json"))
VERBOSE_DISCORD: bool = os.getenv("VERBOSE_DISCORD", "false").lower() in {"1","true","yes","on"}
PER_ASSET_JITTER: float = float(os.getenv("PER_ASSET_JITTER", "0.6"))
CONFIDENCE_THRESHOLD: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.60"))

# Pré-alertas (mantidos para evolução futura)
PRE_ALERTS: bool = os.getenv("PRE_ALERTS", "true").lower() in {"1","true","yes","on"}
PRE_ALERT_WINDOW_SEC: int = int(os.getenv("PRE_ALERT_WINDOW_SEC", "1200"))
PRE_ALERT_MIN_SCORE: float = float(os.getenv("PRE_ALERT_MIN_SCORE", "0.50"))
PRE_ALERT_IMPROVE_DELTA: float = float(os.getenv("PRE_ALERT_IMPROVE_DELTA", "0.07"))
REQUIRE_PRE_FOR_ALERT: bool = os.getenv("REQUIRE_PRE_FOR_ALERT", "false").lower() in {"1","true","yes","on"}

# Backend
BACKEND_URL: Optional[str] = os.getenv("BACKEND_URL")  # ex: http://127.0.0.1:8080

# Targets (configuráveis)
TP1_PCT: float = float(os.getenv("TP1_PCT", "0.006"))   # 0.6%
TP2_PCT: float = float(os.getenv("TP2_PCT", "0.012"))   # 1.2%
TP3_PCT: float = float(os.getenv("TP3_PCT", "0.018"))   # 1.8%
SL_PCT:  float = float(os.getenv("SL_PCT",  "0.0035"))  # 0.35%

# ===== Estado/cooldown =====
_state_lock = asyncio.Lock()
_state: Dict[str, Any] = {}

def _load_state() -> None:
    global _state
    try:
        if os.path.exists(STATE_PATH):
            with open(STATE_PATH, "r") as f:
                _state = json.load(f)
    except Exception as e:
        print(f"⚠️ Falha ao carregar STATE {STATE_PATH}: {e}")

def _save_state() -> None:
    try:
        tmp = STATE_PATH + ".tmp"
        with open(tmp, "w") as f:
            json.dump(_state, f)
        os.replace(tmp, STATE_PATH)
    except Exception as e:
        print(f"⚠️ Falha ao salvar STATE {STATE_PATH}: {e}")

def _can_send(symbol: str, status: str) -> bool:
    node = _state.get(symbol, {})
    last_status = node.get("last_status")
    last_ts = node.get("last_sent_ts", 0)
    now = int(time.time())
    return status != last_status or (now - last_ts) >= MESSAGE_COOLDOWN

def _mark_sent(symbol: str, status: str) -> None:
    node = _state.get(symbol, {})
    node["last_status"] = status
    node["last_sent_ts"] = int(time.time())
    _state[symbol] = node
    _save_state()

# ===== Helpers =====
def _fmt_price(p: Optional[float]) -> str:
    if p is None:
        return "-"
    # 6 casas por padrão para pares cripto spot comuns
    return f"{p:.6f}"

def _compute_targets(entry: float, direction: str) -> Dict[str, Optional[float]]:
    """
    Retorna TP1/TP2/TP3 e SL conforme direção.
    Apenas TP1/SL são enviados ao backend; todos aparecem no alerta do Discord.
    """
    if entry <= 0 or direction not in {"LONG", "SHORT"}:
        return {"tp1": None, "tp2": None, "tp3": None, "sl": None}

    if direction == "LONG":
        tp1 = entry * (1.0 + TP1_PCT)
        tp2 = entry * (1.0 + TP2_PCT)
        tp3 = entry * (1.0 + TP3_PCT)
        sl  = entry * (1.0 - SL_PCT)
    else:  # SHORT
        tp1 = entry * (1.0 - TP1_PCT)
        tp2 = entry * (1.0 - TP2_PCT)
        tp3 = entry * (1.0 - TP3_PCT)
        sl  = entry * (1.0 + SL_PCT)

    return {"tp1": tp1, "tp2": tp2, "tp3": tp3, "sl": sl}

# ===== Worker =====
async def _worker(symbol: str, sem: asyncio.Semaphore) -> Tuple[Optional[str], Dict[str, Any], Optional[Exception]]:
    await asyncio.sleep(random.random() * PER_ASSET_JITTER)
    async with sem:
        try:
            # analisar_ativo é síncrona → rodar em thread
            msg, ctx = await asyncio.to_thread(analisar_ativo, symbol)

            stages = ctx.get("stages", {})
            status_5m = (stages.get("5m") or {}).get("categoria", "n/a")
            lp = ctx.get("pct_long", 0)
            sp = ctx.get("pct_short", 0)
            conf = float(ctx.get("confidence_score", 0.0))
            direction = ctx.get("direction")
            authorized = bool(ctx.get("authorized"))

            print(f"🧐 {symbol} → {status_5m} | dir={direction} | conf={conf:.2f} | L={lp}% S={sp}%")

            # status "alto nível" para cooldown
            hi_status = ("long" if direction == "LONG" else "short" if direction == "SHORT" else status_5m)

            if authorized and conf >= CONFIDENCE_THRESHOLD and _can_send(symbol, hi_status):
                # Preço e targets
                entry_price = get_current_price(symbol) or 0.0
                targets = _compute_targets(entry_price, direction or "")

                # 1) Discord
                alert_text = (
                    f"**{symbol}** — {direction}\n"
                    f"{msg}\n"
                    f"🎯 Conf: {conf:.2f} | L={lp}% | S={sp}%\n"
                    f"💫 Entry: {_fmt_price(entry_price)} | "
                    f"TP1: {_fmt_price(targets['tp1'])} | TP2: {_fmt_price(targets['tp2'])} | TP3: {_fmt_price(targets['tp3'])} | "
                    f"SL: {_fmt_price(targets['sl'])}"
                )
                enviar_alerta_entrada(alert_text, confidence_score=conf)

                # 2) Backend (se configurado) — envia TP1/SL principais
                if BACKEND_URL:
                    try:
                        payload = {
                            "symbol": symbol,
                            "direction": (direction or "").lower(),
                            "interval": "5m",
                            "entry_price": round(float(entry_price), 6) if entry_price else None,
                            "tp": round(float(targets["tp1"]), 6) if targets["tp1"] else None,
                            "sl": round(float(targets["sl"]), 6) if targets["sl"] else None,
                            "status": "open",
                            "timestamp": datetime.utcnow().isoformat()
                        }
                        r = requests.post(f"{BACKEND_URL}/calls/", json=payload, timeout=6)
                        if 200 <= r.status_code < 300:
                            print(f"📡 Call enviada ao backend: {symbol} ({direction})")
                        else:
                            print(f"⚠️ Falha ao enviar call para backend: {r.status_code} {r.text}")
                    except Exception as e:
                        print(f"❌ Erro ao enviar call para backend: {e}")

                async with _state_lock:
                    _mark_sent(symbol, hi_status)

            elif VERBOSE_DISCORD and _can_send(symbol, hi_status):
                enviar_relatorio(f"🛰️ {symbol} — {status_5m}\n{msg}\n📊 Conf: {conf:.2f} | L={lp}% | S={sp}%")
                async with _state_lock:
                    _mark_sent(symbol, hi_status)

            return msg, ctx, None

        except Exception as e:
            print(f"❌ Worker erro {symbol}: {e}")
            return None, {"symbol": symbol, "error": str(e)}, e

# ===== Loop principal =====
_stop_flag = False
def _graceful_stop(*_):
    global _stop_flag
    _stop_flag = True
    print("🛑 Execução interrompida — finalizando após a rodada atual.")

async def sentinela():
    _load_state()
    print("🛰️ CharlieCore Sentinel iniciado.")
    print(f"⏱️ Intervalo: {INTERVAL}s | 🎯 Ativos: {', '.join(ASSETS)} | ⚙️ Conc: {CONCURRENCY}")
    print(f"🧪 Verbose Discord: {VERBOSE_DISCORD} | Cooldown: {MESSAGE_COOLDOWN}s | Threshold: {CONFIDENCE_THRESHOLD:.2f}")
    print(f"🔎 Pré-alerta: {'ON' if PRE_ALERTS else 'OFF'} | Janela={PRE_ALERT_WINDOW_SEC}s | MinScore={PRE_ALERT_MIN_SCORE:.2f} | Δ+={PRE_ALERT_IMPROVE_DELTA:.2f} | RequirePre={REQUIRE_PRE_FOR_ALERT}")
    if BACKEND_URL:
        print(f"🌐 Backend URL: {BACKEND_URL}")
    print(f"🎯 Targets: TP1={TP1_PCT:.4f} TP2={TP2_PCT:.4f} TP3={TP3_PCT:.4f} | SL={SL_PCT:.4f}")

    while not _stop_flag:
        try:
            print(f"📡 Nova varredura — {datetime.utcnow().isoformat(timespec='seconds')}")
            sem = asyncio.Semaphore(CONCURRENCY)
            tasks = [asyncio.create_task(_worker(sym, sem)) for sym in ASSETS]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            calls_ok = 0
            errors = 0
            for res in results:
                if isinstance(res, Exception):
                    errors += 1
                    continue
                _msg, ctx, err = res  # type: ignore
                if err:
                    errors += 1
                elif isinstance(ctx, dict) and ctx.get("authorized"):
                    calls_ok += 1

            print(f"📊 Calls autorizadas nesta rodada: {calls_ok} | ❗Erros: {errors}")

        except Exception as e:
            print(f"💥 Falha no loop principal: {e}")

        for _ in range(INTERVAL):
            if _stop_flag:
                break
            await asyncio.sleep(1)

    print("✅ Sentinel finalizado com segurança.")

if __name__ == "__main__":
    signal.signal(signal.SIGINT, _graceful_stop)
    signal.signal(signal.SIGTERM, _graceful_stop)
    asyncio.run(sentinela())
