import pandas as pd

class Indicators:

    def calculate_ema(self, df, period):
        """
        Calculates the Exponential Moving Average (EMA) for the given period.
        :param df: DataFrame containing historical price data, with a 'close' column.
        :param period: The period over which to calculate the EMA.
        :return: A Pandas Series representing the EMA.
        """
        ema = df['close'].ewm(span=period, adjust=False).mean()
        return ema
    
    def calculate_rsi(self, df, period=14):
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0.0)
        loss = -delta.where(delta < 0, 0.0)
        avg_gain = gain.rolling(window=period, min_periods=1).mean()
        avg_loss = loss.rolling(window=period, min_periods=1).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def calculate_bollinger_bands(self, df, period=20, std_dev=2):
        sma = df['close'].rolling(window=period).mean()
        rolling_std = df['close'].rolling(window=period).std()
        upper_band = sma + (rolling_std * std_dev)
        lower_band = sma - (rolling_std * std_dev)
        return upper_band, lower_band
