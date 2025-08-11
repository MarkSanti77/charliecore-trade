# supertrend.py — Indicador Supertrend para a CharlieCore

import pandas as pd
import numpy as np

class Supertrend:
    def __init__(self, high, low, close, window=10, multiplier=3.0):
        """
        Inicializa o indicador Supertrend.

        Parâmetros:
        - high: Série de preços máximos
        - low: Série de preços mínimos
        - close: Série de preços de fechamento
        - window: Janela de cálculo do ATR
        - multiplier: Fator de multiplicação do ATR
        """
        self.high = high
        self.low = low
        self.close = close
        self.window = window
        self.multiplier = multiplier

    def _calculate_atr(self):
        """
        Calcula o Average True Range (ATR) necessário para o Supertrend.
        """
        high = self.high
        low = self.low
        close = self.close

        tr1 = high - low
        tr2 = (high - close.shift(1)).abs()
        tr3 = (low - close.shift(1)).abs()

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(self.window).mean()

        return atr

    def supertrend_direction(self):
        """
        Retorna a direção da tendência:
        - 1: Tendência de alta
        - -1: Tendência de baixa
        """
        atr = self._calculate_atr()
        hl2 = (self.high + self.low) / 2
        upperband = hl2 + self.multiplier * atr
        lowerband = hl2 - self.multiplier * atr

        final_upperband = upperband.copy()
        final_lowerband = lowerband.copy()

        direction = pd.Series(index=self.close.index, dtype=int)
        direction.iloc[0] = 1  # Assume tendência de alta no início

        for i in range(1, len(self.close)):
            if self.close[i] > final_upperband[i - 1]:
                direction.iloc[i] = 1
            elif self.close[i] < final_lowerband[i - 1]:
                direction.iloc[i] = -1
            else:
                direction.iloc[i] = direction.iloc[i - 1]

                # Ajusta bandas para evitar inversões falsas
                if direction.iloc[i] == 1 and lowerband[i] < final_lowerband[i - 1]:
                    final_lowerband[i] = final_lowerband[i - 1]
                if direction.iloc[i] == -1 and upperband[i] > final_upperband[i - 1]:
                    final_upperband[i] = final_upperband[i - 1]

        return direction
