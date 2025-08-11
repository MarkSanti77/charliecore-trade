# messages.py — Central de formatação e envio (anti-spam por ativo + preço atual)
from __future__ import annotations
import os, json, time
from typing import Dict, Any
import requests
from data import get_current_price  # importa para pegar o preço ao vivo

STATE_PATH = os.getenv("CHARLIE_STATE_PATH", ".charlie_state.json")

# ---------------- State helpers ----------------
def _load_state() -> Dict[str, Any]:
    try:
        with open(STATE_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def _save_state(state: Dict[str, Any]) -> None:
    tmp = f"{STATE_PATH}.tmp"
    with open(tmp, "w") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    os.replace(tmp, STATE_PATH)

def _normalize_status(ctx: Dict[str, Any]) -> str:
    """Resumo do status para dedupe (por timeframe)."""
    try:
        stages = ctx.get("stages", {})
        return json.dumps({
            "4h": stages.get("4h", {}).get("categoria"),
            "1h": stages.get("1h", {}).get("categoria"),
            "15m": stages.get("15m", {}).get("categoria"),
            "5m": stages.get("5m", {}).get("categoria"),
        }, sort_keys=True)
    except Exception:
        return "unknown"

# ---------------- Formatter ----------------
def format_discord_message(texto: str, contexto: Dict[str, Any]) -> str:
    symbol = (contexto or {}).get("symbol") or os.getenv("SYMBOL", "—")

    # Pega preço atual (falha silenciosa se API fora)
    try:
        preco = get_current_price(symbol)
        preco_fmt = f"{preco:,.2f}" if preco is not None else "—"
    except Exception:
        preco_fmt = "—"

    stages = contexto.get("stages", {})

    def line(tf: str) -> str:
        s = stages.get(tf, {})
        cat = s.get('categoria', '?')
        msg = s.get('msg', '')
        return f"**{tf}**: {cat} — {msg}"

    detalhes = "\n".join([line("4h"), line("1h"), line("15m"), line("5m")])
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    return f"**{symbol}** — 💵 {preco_fmt} — {texto}\n\n{detalhes}\n\n`{ts}`"

# ---------------- Sender (with per-symbol anti-spam) ----------------
def send_discord_message(texto: str, contexto: Dict[str, Any], *, force: bool=False) -> bool:
    webhook = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook:
        print("❌ DISCORD_WEBHOOK_URL não configurado.")
        return False

    symbol = (contexto or {}).get("symbol") or os.getenv("SYMBOL", "GLOBAL")
    current_sig = _normalize_status(contexto)
    cooldown = int(os.getenv("MESSAGE_COOLDOWN_SECONDS", "120"))
    now = time.time()

    # Carrega state e garante estrutura por símbolo
    state = _load_state()
    symbols_state = state.get("symbols")
    if not isinstance(symbols_state, dict):
        symbols_state = {}
        if "last_signature" in state or "last_sent_ts" in state:
            symbols_state[symbol] = {
                "last_signature": state.get("last_signature"),
                "last_sent_ts": state.get("last_sent_ts", 0),
            }
        state["symbols"] = symbols_state

    sym_state = symbols_state.get(symbol, {"last_signature": None, "last_sent_ts": 0})
    last_sig = sym_state.get("last_signature")
    last_ts = float(sym_state.get("last_sent_ts") or 0)

    # Anti-spam por símbolo
    if not force and last_sig == current_sig and (now - last_ts) < cooldown:
        print(f"⏸️ Mensagem suprimida ({symbol}): status idêntico e dentro do cooldown.")
        return True

    content = format_discord_message(texto, contexto)
    payload = {"content": content}

    try:
        r = requests.post(webhook, json=payload, timeout=10)
        if r.status_code // 100 == 2:
            sym_state["last_signature"] = current_sig
            sym_state["last_sent_ts"] = now
            symbols_state[symbol] = sym_state
            state["symbols"] = symbols_state
            _save_state(state)
            print(f"✅ Mensagem enviada ao Discord ({symbol}).")
            return True
        else:
            print(f"❌ Falha ao enviar mensagem ({r.status_code}): {r.text}")
            return False
    except Exception as e:
        print(f"❌ Erro de rede ao enviar ao Discord: {e}")
        return False
