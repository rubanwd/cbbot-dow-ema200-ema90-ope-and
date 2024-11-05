# strategy.py

import pandas as pd
from helpers import Helpers
from indicators import Indicators

class Strategies:
    def __init__(self):
        self.indicators = Indicators()

    def prepare_dataframe(self, historical_data):
        df = pd.DataFrame(historical_data)
        df.columns = ["timestamp", "open", "high", "low", "close", "volume", "turnover"]
        df['close'] = df['close'].astype(float)
        df.sort_values('timestamp', inplace=True)
        return df

    def multi_timeframe_dow_strategy(self, d1_df, h4_df, h1_df):
        # Determine trend on the larger timeframes
        print("Calculating trend for D1 timeframe...")
        d1_trend = self.indicators.calculate_trend_direction(d1_df)
        print(f"D1 trend detected: {d1_trend}")

        print("Calculating trend for H4 timeframe...")
        h4_trend = self.indicators.calculate_trend_direction(h4_df)
        print(f"H4 trend detected: {h4_trend}")

        # Check if D1 and H4 trends are aligned
        if d1_trend == h4_trend:
            print(f"D1 and H4 trends are aligned: {d1_trend}")

            # Calculate MACD on H1 for trade trigger
            print("Calculating MACD for H1 timeframe...")
            macd, macd_signal = self.indicators.calculate_macd(h1_df)
            current_macd = macd.iloc[-1]
            current_macd_signal = macd_signal.iloc[-1]

            print(f"H1 MACD: {current_macd}, MACD Signal: {current_macd_signal}")

            # If both trends are up and MACD shows bullish signal, go long
            if d1_trend == 'uptrend' and current_macd > current_macd_signal:
                print("MACD indicates a bullish entry signal. Going long.")
                return 'long'

            # If both trends are down and MACD shows bearish signal, go short
            elif d1_trend == 'downtrend' and current_macd < current_macd_signal:
                print("MACD indicates a bearish entry signal. Going short.")
                return 'short'

            else:
                print("MACD does not confirm trend continuation. No trade signal.")
                return None
        else:
            print(f"D1 and H4 trends are not aligned. No trade signal.")
            return None


