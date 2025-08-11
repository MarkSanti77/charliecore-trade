# tracker/utils.py 🚀 Performance Tracker - CharlieCore Supreme

import csv
import os

CALLS_CSV_PATH = "tracker/calls.csv"

def salvar_call(symbol, direction, interval, entry_price, tp, sl, timestamp,
                status="ativa", exit_price="", exit_time=""):
    """
    Salva uma call em tracker/calls.csv com os dados essenciais da operação.
    
    Parâmetros:
        symbol (str): Par analisado (ex: BTCUSDT)
        direction (str): Direção da operação (LONG ou SHORT)
        interval (str): Intervalo gráfico (ex: 15m, 1h)
        entry_price (float): Preço de entrada
        tp (float): Take Profit
        sl (float): Stop Loss
        timestamp (str): Data e hora da entrada
        status (str): Status atual da operação (ativa, encerrada)
        exit_price (str): Preço de saída (se encerrado)
        exit_time (str): Timestamp de saída (se encerrado)
    """

    os.makedirs(os.path.dirname(CALLS_CSV_PATH), exist_ok=True)

    nova_linha = {
        "symbol": symbol,
        "direction": direction,
        "interval": interval,
        "entry_price": round(entry_price, 4),
        "tp": round(tp, 4) if tp else "",
        "sl": round(sl, 4) if sl else "",
        "status": status,
        "timestamp": timestamp,
        "exit_price": exit_price,
        "exit_time": exit_time
    }

    escreve_header = not os.path.exists(CALLS_CSV_PATH)

    with open(CALLS_CSV_PATH, mode="a", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=nova_linha.keys())
        if escreve_header:
            writer.writeheader()
        writer.writerow(nova_linha)

    print(f"✅ Call registrada: {symbol} | {direction} | {interval} | Preço: {entry_price}")
