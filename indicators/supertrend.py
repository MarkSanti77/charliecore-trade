import pandas as pd

class Supertrend:
    def __init__(self, high, low, close, window=10, multiplier=3.0):
        self.high = high
        self.low = low
        self.close = close
        self.window = window
        self.multiplier = multiplier
        self.df = pd.DataFrame({'high': high, 'low': low, 'close': close})
        self._calculate()

    def _calculate(self):
        hl2 = (self.df['high'] + self.df['low']) / 2
        atr = self._atr()
        self.df['upper_band'] = hl2 + (self.multiplier * atr)
        self.df['lower_band'] = hl2 - (self.multiplier * atr)
        self.df['trend'] = True

        for i in range(1, len(self.df)):
            if self.df.loc[i, 'close'] > self.df.loc[i - 1, 'upper_band']:
                self.df.loc[i, 'trend'] = True
            elif self.df.loc[i, 'close'] < self.df.loc[i - 1, 'lower_band']:
                self.df.loc[i, 'trend'] = False
            else:
                self.df.loc[i, 'trend'] = self.df.loc[i - 1, 'trend']
                if self.df.loc[i, 'trend'] and self.df.loc[i, 'lower_band'] < self.df.loc[i - 1, 'lower_band']:
                    self.df.loc[i, 'lower_band'] = self.df.loc[i - 1, 'lower_band']
                if not self.df.loc[i, 'trend'] and self.df.loc[i, 'upper_band'] > self.df.loc[i - 1, 'upper_band']:
                    self.df.loc[i, 'upper_band'] = self.df.loc[i - 1, 'upper_band']

        self.df['supertrend'] = self.df['trend'].apply(lambda x: 1 if x else -1)

    def _atr(self):
        high = self.df['high']
        low = self.df['low']
        close = self.df['close']
        tr1 = high - low
        tr2 = (high - close.shift()).abs()
        tr3 = (low - close.shift()).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return tr.rolling(self.window).mean()

    def supertrend_direction(self):
        return self.df['supertrend']
