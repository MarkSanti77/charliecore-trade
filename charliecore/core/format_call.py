#!/usr/bin/env python3
import argparse, os, sys, yaml

BASE = os.path.dirname(os.path.dirname(__file__))
CFG = os.path.join(BASE, "config", "charliecore_rules.yaml")

def load_rules():
    with open(CFG, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def main():
    p = argparse.ArgumentParser(description="Formatador de CALL CharlieCore")
    p.add_argument("--symbol", required=True, help="Ex: SUIUSDT, SOLUSDT")
    p.add_argument("--setup", required=True, choices=["short_continuacao","long_continuacao"])
    p.add_argument("--side", required=True, choices=["short","long"])
    p.add_argument("--zone", default="PREÇO-ALVO ± 0,5xATR5m")
    p.add_argument("--confs", default="15m/1h alinhados, OBV no sentido, Bollinger abrindo, BTC acoplado 0.78")
    p.add_argument("--timing", default="A (pullback-rejeição)")
    p.add_argument("--validity", default="15–30 min")
    args = p.parse_args()

    rules = load_rules()
    fmt = rules["alert"]["format"]
    setup_num = "1" if args.setup == "short_continuacao" else "2"
    risk_pct = round(rules["setups"][args.setup]["risk"]["risk_per_trade"]*100, 2)

    msg = fmt.format(
        setup=setup_num,
        symbol=args.symbol,
        side=args.side.upper(),
        zone=args.zone,
        confs=args.confs,
        timing=args.timing,
        risk_pct=risk_pct,
        sl="auto (topo/fundo menor)",
        tp1="0,5R",
        tp2="1,0R",
        validity=args.validity
    )
    print(msg)

if __name__ == "__main__":
    sys.exit(main())
