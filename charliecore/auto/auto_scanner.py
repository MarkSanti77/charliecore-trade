import os
from dotenv import load_dotenv
load_dotenv(override=True)

import sys, json, time, subprocess, yaml
import datetime as dt

# === Diretórios base ===
AUTO_DIR = os.path.dirname(os.path.abspath(__file__))
CHARLIECORE_DIR = os.path.dirname(AUTO_DIR)
PROJECT_ROOT = os.path.dirname(CHARLIECORE_DIR)

# === sys.path ===
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if CHARLIECORE_DIR not in sys.path:
    sys.path.insert(0, CHARLIECORE_DIR)

# === Caminhos fixos ===
STATE = os.path.join(PROJECT_ROOT, ".charlie_state.json")
CFG  = os.path.join(CHARLIECORE_DIR, "config", "charliecore_rules.yaml")
MAKE = os.path.join(CHARLIECORE_DIR, "core",   "make_call.sh")

import os
from dotenv import load_dotenv
load_dotenv(override=True)

import sys, json, time, subprocess, yaml
import datetime as dt





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
    setup = "long_continuacao" if sig.get("side")=="long" else "short_continuacao"
    stp   = rules.get("setups",{}).get(setup,{})
    coup_th = ((stp.get("btc_coupling") or {}).get("threshold") or 0.0)
    atr_max = ((stp.get("volatility")  or {}).get("atr_proximity_max") or 1e9)
    if float(sig.get("coupling",0)) >= float(coup_th): score+=1
    else: missing.append("coupling")
    if float(sig.get("atr_proximity",99)) <= float(atr_max): score+=1
    else: missing.append("atr")
    return (score/total >= PRE_MIN, missing, score/total)
def load_yaml(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def load_state():
        return {"last_sent": {}, "last_hash": {}}
        return json.load(f)

def save_state(state):
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

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
    coupling_th = float(stp["btc_coupling"]["threshold"])
    atr_max     = float(stp["volatility"]["atr_proximity_max"])

    # dbg thresholds
    try:
        print(f"dbg_th {sig['symbol']} {sig['side']} coupling_th={coupling_th:.2f} atr_max={atr_max:.2f}")
    except Exception:
        pass

    # 1) Qualidade macro
    if not sig.get("trend_ok"):
        return False, "trend_not_ok"

    # 2) Invalidações
    if sig.get("invalidations", False):
        return False, "invalidated"

    # 3) Coupling (usar YAML)
    if float(sig.get("coupling", 0)) < coupling_th:
        return False, "low_coupling"

    # 4) Proximidade de zona (usar YAML)
    if float(sig.get("atr_proximity", 99)) > atr_max:
        return False, "too_far_from_zone"

    # 5) Bollinger (exceção: flat permitido se acoplado e perto da zona)
    if sig.get("bollinger") != "expanding":
        if float(sig.get("atr_proximity", 99)) <= atr_max and float(sig.get("coupling",0)) >= 0.80:
            pass
        else:
            return False, "bollinger_not_expanding"

    # 6) OBV (bypass quando macro forte + perto da zona + alto acoplamento)
    if not sig.get("obv_ok"):
        macro_ok = sig.get("trend_ok", False)
        near_zone = float(sig.get("atr_proximity", 99)) <= 0.80
        high_coup = float(sig.get("coupling", 0)) >= 0.85
        if macro_ok and near_zone and high_coup:
            pass
        else:
            return False, "obv_not_ok"

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
        print(f"dbg {sig['symbol']} {sig['side']} "
              f"coupling={sig.get('coupling'):.2f} "
              f"atr={sig.get('atr_proximity'):.2f} "
              f"boll={sig.get('bollinger')} "
              f"trend={sig.get('trend_ok')} "
              f"obv={sig.get('obv_ok')}")
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


