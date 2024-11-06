import pandas as pd
from indicators import Indicators
import logging

class Strategies:
    def __init__(self):
        self.indicators = Indicators()

    def prepare_dataframe(self, historical_data):
        """
        Prepares the DataFrame from historical data, sorting and formatting it correctly.
        """
        df = pd.DataFrame(historical_data)
        df.columns = ["timestamp", "open", "high", "low", "close", "volume", "turnover"]
        df['close'] = df['close'].astype(float)
        df.sort_values('timestamp', inplace=True)
        return df

    def ema_trend_strategy(self, df):
        """
        Determines the trend based on EMA-200 and EMA-90.
        Returns 'uptrend' if EMA-90 > EMA-200, otherwise 'downtrend'.
        """
        df['ema_200'] = self.indicators.calculate_ema(df, 200)
        df['ema_90'] = self.indicators.calculate_ema(df, 90)

        ema_200 = df['ema_200'].iloc[-1]
        ema_90 = df['ema_90'].iloc[-1]

        logging.info(f"EMA-200: {ema_200}, EMA-90: {ema_90}")
        return 'uptrend' if ema_90 > ema_200 else 'downtrend'

    def rsi_bollinger_confirmation(self, df, trend):
        """
        Confirms trade signals using RSI or Bollinger Bands.
        - For uptrend: RSI < 40 or close < lower Bollinger Band indicates a buy signal.
        - For downtrend: RSI > 60 or close > upper Bollinger Band indicates a sell signal.
        """
        df['rsi'] = self.indicators.calculate_rsi(df, 14)
        df['bollinger_upper'], df['bollinger_middle'], df['bollinger_lower'] = self.indicators.calculate_bollinger_bands(df)

        latest_close = df['close'].iloc[-1]
        rsi = df['rsi'].iloc[-1]
        lower_band = df['bollinger_lower'].iloc[-1]
        upper_band = df['bollinger_upper'].iloc[-1]

        logging.info(f"RSI: {rsi}, Close: {latest_close}, Bollinger Bands: [{lower_band}, {upper_band}]")

        if trend == 'uptrend':
            if rsi < 40 or latest_close < lower_band:
                logging.info("Buy signal confirmed (RSI < 40 or close < lower Bollinger Band).")
                return 'buy'
        elif trend == 'downtrend':
            if rsi > 60 or latest_close > upper_band:
                logging.info("Sell signal confirmed (RSI > 60 or close > upper Bollinger Band).")
                return 'sell'

        logging.info("No confirmation signal generated.")
        return None
