import os
from dotenv import load_dotenv
load_dotenv(override=True)

import sys, json, time, subprocess, yaml
import datetime as dt

#!/usr/bin/env python3
import sys, json, time, subprocess, yaml, datetime as dt

BASE = os.path.dirname(os.path.dirname(__file__))     # .../charliecore
ROOT = os.path.dirname(BASE)                          # repo root
CFG  = os.path.join(BASE, "config", "charliecore_rules.yaml")
STATE= os.path.join(ROOT, ".charlie_state.json")
MAKE = os.path.join(BASE, "core", "make_call.sh")

def load_yaml(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def load_state():
    if not os.path.exists(STATE):
        return {"last_sent": {}, "last_hash": {}}
    with open(STATE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_state(state):
    tmp = STATE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    os.replace(tmp, STATE)

def sig_key(sig):
    return f"{sig['symbol']}|{sig['side']}"

def sig_hash(sig):
    # assinatura leve pra deduplicar por zona/confluência/timing dentro da janela
    base = f"{sig['symbol']}|{sig['side']}|{sig.get('confs','')}|{sig.get('timing','')}"
    return str(abs(hash(base)) % (10**8))

def should_send(sig, rules, state, now):
    # thresholds do YAML
    setup = "long_continuacao" if sig["side"]=="long" else "short_continuacao"
    stp   = rules["setups"][setup]
    coupling_th = stp["btc_coupling"]["threshold"]
    atr_max     = stp["volatility"]["atr_proximity_max"]

    # Filtros de qualidade
    if not sig.get("trend_ok"): return False, "trend_not_ok"
    if not sig.get("obv_ok"):   return False, "obv_not_ok"
    if sig.get("bollinger") != "expanding": return False, "bollinger_not_expanding"
    if sig.get("invalidations", False):     return False, "invalidated"
    if sig.get("coupling", 0) < coupling_th: return False, "low_coupling"
    if sig.get("atr_proximity", 1) > atr_max: return False, "too_far_from_zone"

    # Anti-spam: cooldown por par/direção
    key = sig_key(sig)
    last_sent_ts = state.get("last_sent", {}).get(key)
    COOLDOWN_MIN = int(os.getenv('AUTO_COOLDOWN_MIN','20'))  # minutos (ajuste se quiser)
    if last_sent_ts:
        delta_min = (now - dt.datetime.fromisoformat(last_sent_ts)).total_seconds() / 60.0
        if delta_min < COOLDOWN_MIN:
            return False, f"cooldown_{int(COOLDOWN_MIN - delta_min)}m"

    # Anti-duplicado: mesma assinatura nas últimas 6h
    h = sig_hash(sig)
    last = state.get("last_hash", {}).get(key)
    if last and last["hash"] == h:
        ago_min = (now - dt.datetime.fromisoformat(last["ts"])).total_seconds()/60.0
        if ago_min < 360:  # 6h
            return False, "duplicate_hash"

    return True, "ok"

def send_call(sig):
    setup = "long_continuacao" if sig["side"]=="long" else "short_continuacao"
    confs = sig.get("confs", "15m/1h alinhados, OBV no sentido, Bollinger abrindo, BTC acoplado")
    timing= sig.get("timing", "A (pullback-rejeição)")
    cmd = [MAKE, sig["symbol"], setup, sig["side"], confs, timing]
    # Executa via bash
    subprocess.run(cmd, check=True)

def main():
    # tenta importar os candidatos do seu scanner.py
    sys.path.insert(0, ROOT)
    try:
        from scanner import get_candidates
    except Exception as e:
        print("ERRO: scanner.get_candidates não disponível:", e)
        return 1

    rules = load_yaml(CFG)
    state = load_state()
    now = dt.datetime.now()

    candidates = get_candidates() or []
    if not candidates:
        print(f"{now.isoformat()} - nenhum candidato")
        return 0

    sent = 0
    for sig in candidates:
        ok, why = should_send(sig, rules, state, now)
        print(f"cand {sig.get('symbol')} {sig.get('side')} -> {why}")
        if not ok:
            continue
        try:
            send_call(sig)
            sent += 1
            key = sig_key(sig)
            h   = sig_hash(sig)
            state.setdefault("last_sent", {})[key] = now.isoformat()
            state.setdefault("last_hash", {})[key] = {"hash": h, "ts": now.isoformat()}
            save_state(state)
            time.sleep(1)  # respiro
        except Exception as e:
            print("falha ao enviar call:", e)

    print(f"{now.isoformat()} - calls enviadas:", sent)
    return 0

if __name__ == "__main__":
    sys.exit(main())


PRE_ALERTS = os.getenv("PRE_ALERTS","true").lower() not in ("0","false","no")
PRE_WINDOW = int(os.getenv("PRE_ALERT_WINDOW_SEC","900"))
PRE_MIN    = float(os.getenv("PRE_ALERT_MIN_SCORE","0.42"))
PRE_IMP    = float(os.getenv("PRE_ALERT_IMPROVE_DELTA","0.02"))


def almost_ok(sig, rules):
    """Score parcial 0..1 + lista de faltas."""
    missing=[]; score=0; total=6
    if sig.get("trend_ok"): score+=1
    else: missing.append("trend")
    if sig.get("obv_ok"): score+=1
    else: missing.append("obv")
    if sig.get("bollinger")=="expanding": score+=1
    else: missing.append("bollinger")
    if not sig.get("invalidations", False): score+=1
    else: missing.append("invalidation")
    # thresholds do YAML
    setup = "long_continuacao" if sig.get("side")=="long" else "short_continuacao"
    stp   = rules.get("setups",{}).get(setup,{})
    coup_th = ((stp.get("btc_coupling") or {}).get("threshold") or 0.0)
    atr_max = ((stp.get("volatility")  or {}).get("atr_proximity_max") or 1e9)
    if float(sig.get("coupling",0)) >= float(coup_th): score+=1
    else: missing.append("coupling")
    if float(sig.get("atr_proximity",99)) <= float(atr_max): score+=1
    else: missing.append("atr")
    return (score/total >= PRE_MIN, missing, score/total)