# estrategia.py 🧠 CharlieCore Tactical Logic v1.0
# Protocolo: Confirmar entrada apenas se RSI no 5m iniciar novo ciclo com OBV e Supertrend alinhados.

def avaliar_estrategia(rsi, obv, supertrend, intervalo):
    """
    Avalia a estratégia com base nos indicadores.
    Entrada autorizada somente no 5m com:
    - RSI iniciando novo ciclo (subindo de <30 para >35) → LONG
    - RSI iniciando novo ciclo (caindo de >70 para <65) → SHORT
    - E supertrend alinhado + OBV em volume crescente
    """

    # Estratégia geral apenas para relatório (4h, 15m, 1h)
    if intervalo != "5m":
        if supertrend > 0 and rsi > 50:
            return "Tendência de Alta - Acompanhar possível entrada"
        elif supertrend < 0 and rsi < 50:
            return "Tendência de Baixa - Acompanhar possível entrada"
        else:
            return "Sem sinal claro - Observar evolução"
    
    # Lógica de ENTRADA no 5m:
    if rsi > 35 and supertrend > 0 and obv > 0:
        return "✅ entrada LONG autorizada"
    elif rsi < 65 and supertrend < 0 and obv < 0:
        return "⚠️ entrada SHORT autorizada"
    
    return "⏸ Sem confirmação de entrada - Monitorando 5m"
