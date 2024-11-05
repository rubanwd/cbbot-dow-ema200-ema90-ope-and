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
from helpers import Helpers

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
        self.last_closed_position_time = 0

    def check_last_position_time(self):
        last_closed_position = self.data_fetcher.get_last_closed_position(self.symbol)
        if last_closed_position:
            last_closed_time = int(last_closed_position['updatedTime']) / 1000
            time_since_last_close = time.time() - last_closed_time
            if time_since_last_close < 1800:  # 30 minutes = 1800 seconds
                logging.info("Last closed position was less than 30 minutes ago. Skipping trade.")
                return False
        return True

    def close_position_if_trend_changed(self, trend):
        """
        Closes the open position if the trend has changed.
        Returns True if a position was closed, False otherwise.
        """
        open_positions = self.data_fetcher.get_open_positions(self.symbol)
        if open_positions:
            current_position = open_positions[0]  # Assume only one open position at a time
            position_side = current_position['side']

            # Determine if the trend change requires closing the position
            if (trend == 'uptrend' and position_side == 'Sell') or (trend == 'downtrend' and position_side == 'Buy'):
                logging.info(f"Trend changed to {trend}. Closing open position: {position_side}.")
                close_side = 'Buy' if position_side == 'Sell' else 'Sell'
                self.data_fetcher.place_order(
                    symbol=self.symbol,
                    side=close_side,
                    qty=self.quantity,
                    current_price=self.data_fetcher.get_real_time_price(self.symbol),
                    leverage=10,
                )
                return True  # Position was closed due to trend change
            else:
                logging.info(f"No trend change detected. Current position side: {position_side}, trend: {trend}.")
                return False  # No position closed because trend didn’t change as needed
        else:
            logging.info("No open positions to check for trend change.")
            return False  # No position to close because none was open


    def job(self):
        logging.info("-------------------- Bot Iteration --------------------")

        # Fetch 15-minute data to determine trend and H1 data for MACD
        logging.info("Fetching 15-minute (M15) data for trend detection...")
        m15_data = self.data_fetcher.get_historical_data(self.symbol, '15', 100)
        logging.info("Fetching 1-hour (H1) data for MACD confirmation...")
        h1_data = self.data_fetcher.get_historical_data(self.symbol, '60', 100)

        if not m15_data or not h1_data:
            logging.warning("Failed to fetch data for required timeframes.")
            return

        # Prepare dataframes
        m15_df = self.strategy.prepare_dataframe(m15_data)
        h1_df = self.strategy.prepare_dataframe(h1_data)

        # Determine trend based on EMA-200 and EMA-90 on M15
        trend = self.strategy.ema_trend_strategy(m15_df)
        logging.info(f"15-min Trend: {trend}")

        # Map trend to 'long'/'short' for risk management compatibility
        trade_direction = 'long' if trend == 'uptrend' else 'short'

        # Check for open positions and close if trend has changed
        open_positions = self.data_fetcher.get_open_positions(self.symbol)
        if open_positions:
            logging.info("An open position exists. Checking for trend change.")
            position_closed = self.close_position_if_trend_changed(trend)
            if position_closed:
                logging.info("Position closed due to trend change. Skipping new trade entry.")
                return  # Exit after closing the position
            else:
                logging.info("Trend has not changed enough to close the position.")
                return  # Skip trade entry since a position is still open

        # Check if sufficient time has passed since the last closed position
        if not self.check_last_position_time():
            return

        # Confirm trade entry with MACD on H1
        macd_signal = self.strategy.macd_confirmation(h1_df)
        if trend and macd_signal:
            stop_loss, take_profit = self.risk_management.calculate_risk_management(h1_df, trade_direction)
            side = 'Buy' if trade_direction == 'long' else 'Sell'

            logging.info(f"MACD confirmation: {macd_signal} - Placing {side} order.")
            order_result = self.data_fetcher.place_order(
                symbol=self.symbol,
                side=side,
                qty=self.quantity,
                current_price=h1_df['close'].iloc[-1],
                leverage=10,
                # stop_loss=stop_loss,
                take_profit=take_profit
            )

            if order_result:
                logging.info(f"Order successfully placed: {order_result}")
            else:
                logging.error("Failed to place order.")
        else:
            logging.info("No trade signal generated.")




    def run(self):
        self.job()  # Execute once immediately
        schedule.every(1).minutes.do(self.job)  # Run every minute

        while True:
            schedule.run_pending()
            time.sleep(1)

if __name__ == "__main__":
    bot = TradingBot()
    bot.run()
