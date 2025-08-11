#!/usr/bin/env bash
set -e

SYMBOL="$1"
SETUP="$2"
SIDE="$3"
CONF="${4:-15m/1h alinhados, OBV no sentido, Bollinger abrindo, BTC acoplado 0.78}"
TIM="${5:-A (pullback-rejeição)}"

python charliecore/core/format_call.py \
  --symbol "$SYMBOL" \
  --setup "$SETUP" \
  --side "$SIDE" \
  --confs "$CONF" \
  --timing "$TIM"

printf "%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n" \
  "$(date -Iseconds)Z" "$SYMBOL" "$SETUP" "$SIDE" "zona placeholder" "auto" "0,5R" "1,0R" "0,75%" "0.78" "A" "N" "0.0" "manual log" \
  >> charliecore/calls_log.csv
