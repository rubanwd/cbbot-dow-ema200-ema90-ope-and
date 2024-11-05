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

    def rsi_bollinger_confirmation(self, df, trend):
        """
        Confirms buy/sell signals using RSI and Bollinger Bands, with signals aligned to the current trend.
        :param df: DataFrame containing historical data.
        :param trend: The current trend ('uptrend' or 'downtrend') determined by EMA strategy.
        :return: 'buy' for a buy signal, 'sell' for a sell signal, or None if no signal.
        """
        # Calculate RSI and Bollinger Bands
        rsi = self.indicators.calculate_rsi(df, period=14)
        upper_band, lower_band = self.indicators.calculate_bollinger_bands(df, period=20, std_dev=2)

        # Get the latest values
        latest_rsi = rsi.iloc[-1]
        latest_close = df['close'].iloc[-1]
        latest_upper_band = upper_band.iloc[-1]
        latest_lower_band = lower_band.iloc[-1]

        logging.info(f"Latest RSI: {latest_rsi}, Close: {latest_close}, Upper Band: {latest_upper_band}, Lower Band: {latest_lower_band}")

        # Define signals according to the trend
        if trend == 'uptrend':
            if latest_rsi < 40 or latest_close < latest_lower_band:
                logging.info("RSI and Bollinger Bands signal a potential buy entry aligned with uptrend.")
                return 'buy'  # Buy signal aligned with uptrend
        elif trend == 'downtrend':
            if latest_rsi > 60 or latest_close > latest_upper_band:
                logging.info("RSI and Bollinger Bands signal a potential sell entry aligned with downtrend.")
                return 'sell'  # Sell signal aligned with downtrend

        logging.info("No trade signal generated as conditions did not meet trend alignment.")
        return None  # No signal if conditions do not align with the trend
