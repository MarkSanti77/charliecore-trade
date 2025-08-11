#!/bin/bash

cd /root/charliecore-trade

# Evita múltiplas execuções simultâneas
LOCKFILE="/tmp/charliecore-sentinel.lock"

if [ -f "$LOCKFILE" ]; then
    echo "🚫 Sentinel já está em execução. Abortando..." >> logs/sentinel_cron.log
    exit 1
fi

touch "$LOCKFILE"
echo "✅ Execução iniciada: $(date)" >> logs/sentinel_cron.log

# Executa o container de forma segura
docker compose exec -T charliecore-sentinel python3 sentinel.py >> logs/sentinel_cron.log 2>&1

echo "✅ Execução finalizada: $(date)" >> logs/sentinel_cron.log
rm -f "$LOCKFILE"
