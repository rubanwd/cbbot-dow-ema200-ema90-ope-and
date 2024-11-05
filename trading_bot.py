import schedule
import time
import logging
from data_fetcher import DataFetcher
from indicators import Indicators
from strategies import Strategies
from risk_management import RiskManagement
from dotenv import load_dotenv
import os
import pandas as pd
from bybit_demo_session import BybitDemoSession
from helpers import Helpers  # Import the Helpers module

class TradingBot:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("BYBIT_API_KEY")
        self.api_secret = os.getenv("BYBIT_API_SECRET") 
        if not self.api_key or not self.api_secret:
            raise ValueError("API keys not found. Please set BYBIT_API_KEY and BYBIT_API_SECRET in your .env file.")
        
        self.data_fetcher = BybitDemoSession(self.api_key, self.api_secret)
        self.strategy = Strategies()
        self.indicators = Indicators()
        self.risk_management = RiskManagement()
        self.symbol = os.getenv("TRADING_SYMBOL", 'BTCUSDT')
        self.quantity = float(os.getenv("TRADE_QUANTITY", 0.03))
        self.interval = {'D1': 'D', 'H4': '240', 'H1': '60'}

    def job(self):
        print("--------------------")
        is_open_positions = self.data_fetcher.get_open_positions(self.symbol)
        if is_open_positions:
            print("Open positions exist. Skipping.")
            return
        
        is_open_orders = self.data_fetcher.get_open_orders(self.symbol)
        if is_open_orders:
            print("There is an open limit order. A new order will not be placed.")
            return

        # Fetch historical data for all required timeframes
        try:
            print("Fetching Daily (D1) data...")
            d1_data = self.data_fetcher.get_historical_data(self.symbol, self.interval['D1'], 100)
            # print(f"Daily (D1) data: {d1_data}")
            
            print("Fetching 4-hour (H4) data...")
            h4_data = self.data_fetcher.get_historical_data(self.symbol, self.interval['H4'], 100)
            # print(f"4-hour (H4) data: {h4_data}")
            
            print("Fetching 1-hour (H1) data...")
            h1_data = self.data_fetcher.get_historical_data(self.symbol, self.interval['H1'], 100)
            # print(f"1-hour (H1) data: {h1_data}")
        
        except Exception as e:
            print(f"Error fetching data: {e}")
            return
        
        if not d1_data or len(d1_data) == 0:
            print("D1 data is empty.")
        if not h4_data or len(h4_data) == 0:
            print("H4 data is empty.")
        if not h1_data or len(h1_data) == 0:
            print("H1 data is empty.")

        if not d1_data or not h4_data or not h1_data:
            print("Failed to fetch data for one of the timeframes.")
            return

        # Prepare dataframes
        d1_df = self.strategy.prepare_dataframe(d1_data)
        h4_df = self.strategy.prepare_dataframe(h4_data)
        h1_df = self.strategy.prepare_dataframe(h1_data)

        # Apply strategy based on Dow Theory
        trend = self.strategy.multi_timeframe_dow_strategy(d1_df, h4_df, h1_df)
        if trend:
            stop_loss, take_profit = self.risk_management.calculate_risk_management(h1_df, trend)
            side = 'Buy' if trend == 'long' else 'Sell'

            order_result = self.data_fetcher.place_order(
                symbol=self.symbol,
                side=side,
                qty=self.quantity,
                current_price=h1_df['close'].iloc[-1],
                leverage=10,  # Set leverage dynamically if needed
                # stop_loss=stop_loss,
                take_profit=take_profit
            )

            if order_result:
                print(f"Order successfully placed: {order_result}")
            else:
                print("Failed to place order.")
        else:
            print("No trade signal generated.")

    def run(self):
        self.job()  # Execute once immediately
        
        # Check every 1 minute (customize as needed)
        schedule.every(1).minutes.do(self.job)

        while True:
            schedule.run_pending()
            time.sleep(1)

if __name__ == "__main__":
    bot = TradingBot()
    bot.run()
