# scanner.py — Módulo de análise tática de ativos ⚔️ CharlieCore Tactical Scanner

from estrategia import avaliar_estrategia
from utils import obter_dados
from assets import ativos_monitorados

async def analisar_ativos(simbolo=None, intervalo="5m"):
    """
    Executa a análise tática para um ativo específico e um intervalo definido.
    Retorna a call detectada, se houver.
    """
    if simbolo is None:
        return None  # Nenhum ativo especificado

    print(f"\n🧐 Ativo Monitorado: {simbolo} | Intervalo: {intervalo}")
    dados = obter_dados(simbolo, intervalo)

    if not dados:
        print(f"   ⚠️ Dados insuficientes para {simbolo} em {intervalo}.")
        return None

    resultado = avaliar_estrategia(
        rsi=dados.get("rsi"),
        obv=dados.get("obv"),
        supertrend=dados.get("supertrend"),
        interval=intervalo,
        macd=dados.get("macd"),
        macd_signal=dados.get("macd_signal"),
        macd_hist=dados.get("macd_hist"),
        stoch_k=dados.get("stoch_k"),
        stoch_d=dados.get("stoch_d"),
        adx=dados.get("adx"),
        bb_high=dados.get("bb_high"),
        bb_low=dados.get("bb_low"),
        ema_9=dados.get("ema_9"),
        ema_21=dados.get("ema_21"),
        ema_200=dados.get("ema_200"),
        atr=dados.get("atr"),
        price=dados.get("price"),
    )

    print(f"   {resultado}")

    if resultado.startswith("✅ Entrada LONG") or resultado.startswith("⚠️ Entrada SHORT"):
        return {
            "ativo": simbolo,
            "intervalo": intervalo,
            "mensagem": resultado,
            "direcao": "LONG" if "LONG" in resultado else "SHORT"
        }

    return None
