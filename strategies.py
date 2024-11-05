# strategy.py

import pandas as pd
from indicators import Indicators
import logging

class Strategies:
    def __init__(self):
        self.indicators = Indicators()

    def prepare_dataframe(self, historical_data):
        df = pd.DataFrame(historical_data)
        df.columns = ["timestamp", "open", "high", "low", "close", "volume", "turnover"]
        df['close'] = df['close'].astype(float)
        df.sort_values('timestamp', inplace=True)
        return df

    def ema_trend_strategy(self, df):
        ema_200 = self.indicators.calculate_ema(df, 200)
        ema_90 = self.indicators.calculate_ema(df, 90)
        df['ema_200'] = ema_200
        df['ema_90'] = ema_90

        logging.info(f"EMA-200: {ema_200.iloc[-1]}, EMA-90: {ema_90.iloc[-1]}")
        return 'uptrend' if ema_200.iloc[-1] < ema_90.iloc[-1] else 'downtrend'

    def macd_confirmation(self, df):
        macd, macd_signal = self.indicators.calculate_macd(df)
        current_macd = macd.iloc[-1]
        current_macd_signal = macd_signal.iloc[-1]

        logging.info(f"H1 MACD: {current_macd}, MACD Signal: {current_macd_signal}")
        return 'buy' if current_macd > current_macd_signal else 'sell' if current_macd < current_macd_signal else None
