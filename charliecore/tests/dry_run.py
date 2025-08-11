# Dry-run: demonstra pipeline de alerta sem acessar mercado.
import csv, datetime, os, yaml

BASE = os.path.dirname(os.path.dirname(__file__))
CFG = os.path.join(BASE, "config", "charliecore_rules.yaml")
LOG = os.path.join(BASE, "calls_log.csv")

def load_rules():
    with open(CFG, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def format_alert(rules, symbol, setup, side):
    fmt = rules["alert"]["format"]
    data = {
        "setup": "1" if setup=="short_continuacao" else "2",
        "symbol": symbol,
        "side": side.upper(),
        "zone": "PREÇO-ALVO ± 0,5xATR5m",
        "confs": "15m/1h alinhados, OBV no sentido, Bollinger abrindo, BTC acoplado 0.78",
        "timing": "A (pullback-rejeição)",
        "risk_pct": round(rules["setups"][setup]["risk"]["risk_per_trade"]*100, 2),
        "sl": "auto (topo/fundo menor)",
        "tp1": "0,5R",
        "tp2": "1,0R",
        "validity": "15–30 min"
    }
    return fmt.format(**data)

def log_call(symbol, setup, side, executed=False, result_R=0.0, notes="dry-run"):
    exists = os.path.exists(LOG)
    with open(LOG, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if not exists:
            w.writerow(["timestamp","symbol","setup","side","zone","sl","tp1","tp2","risk","btc_coupling","timing","executed","result_R","notes"])
        w.writerow([datetime.datetime.utcnow().isoformat()+"Z", symbol, setup, side, "zona placeholder",
                    "auto", "0,5R", "1,0R", "0,75%", "0.78", "A", "N" if not executed else "Y", result_R, notes])

if __name__ == "__main__":
    rules = load_rules()
    ex1 = format_alert(rules, "SUIUSDT", "short_continuacao", "short")
    ex2 = format_alert(rules, "SOLUSDT", "long_continuacao", "long")
    print(ex1)
    print("-"*60)
    print(ex2)
    log_call("SUIUSDT","short_continuacao","short", executed=False, notes="dry-run exemplo 1")
    log_call("SOLUSDT","long_continuacao","long", executed=False, notes="dry-run exemplo 2")
    print("\nRegistros adicionados em calls_log.csv (modo dry-run).")
