#!/usr/bin/env python3
import argparse, os, yaml

BASE = os.path.dirname(os.path.dirname(__file__))
CFG  = os.path.join(BASE, "config", "charliecore_rules.yaml")

def load_universe():
    with open(CFG, "r", encoding="utf-8") as f:
        rules = yaml.safe_load(f)
    return rules.get("assets", {}).get("universe", [])

def build_cmd(symbol, side, confs, timing):
    setup = "long_continuacao" if side == "long" else "short_continuacao"
    return f'./charliecore/core/make_call.sh {symbol} {setup} {side} "{confs}" "{timing}"'

def main():
    ap = argparse.ArgumentParser(description="Scanner manual: imprime comandos de call para os símbolos do universe")
    ap.add_argument("--side", choices=["long","short","both"], default="both", help="Tipo de calls a listar")
    ap.add_argument("--symbols", nargs="*", help="Filtrar por símbolos específicos (ex: BTCUSDT ETHUSDT)")
    ap.add_argument("--confs", default="15m/1h alinhados, OBV no sentido, Bollinger abrindo, BTC acoplado 0.78",
                    help="Texto das Confluências")
    ap.add_argument("--timing", default="A (pullback-rejeição)", help="Texto do Timing 5m RSI (A|B|C)")
    args = ap.parse_args()

    uni = load_universe()
    if args.symbols:
        # mantém ordem do filtro, só incluindo os que existem no universe
        filter_set = {s.upper() for s in args.symbols}
        uni = [s for s in uni if s.upper() in filter_set]

    if not uni:
        print("Nenhum símbolo no universe (ou filtro vazio).")
        return

    print("### Scanner manual — comandos sugeridos\n")
    for sym in uni:
        if args.side in ("long","both"):
            print(build_cmd(sym, "long", args.confs, args.timing))
        if args.side in ("short","both"):
            print(build_cmd(sym, "short", args.confs, args.timing))
        print()  # linha em branco entre símbolos

if __name__ == "__main__":
    main()
