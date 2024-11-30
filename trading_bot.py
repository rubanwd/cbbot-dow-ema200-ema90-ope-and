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
        self.strategy = Strategies(self.data_fetcher)
        self.indicators = Indicators()
        self.risk_management = RiskManagement()
        self.symbol = os.getenv("TRADING_SYMBOL", 'BTCUSDT')
        self.quantity = float(os.getenv("TRADE_QUANTITY", 0.03))
        self.last_closed_position_time = 0
        self.stop_bot = False  # Flag to stop the bot

    def check_last_position_time(self):
        try:
            last_closed_position = self.data_fetcher.get_last_closed_position(self.symbol)
            if last_closed_position:
                last_closed_time = int(last_closed_position['updatedTime']) / 1000
                time_since_last_close = time.time() - last_closed_time
                if time_since_last_close < 120:  # 2 minutes = 120 seconds
                    logging.info("Last closed position was less than 2 minutes ago. Skipping trade.")
                    return False
            return True
        except Exception as e:
            logging.error(f"Error checking last position time: {e}")
            return False

    def close_position_if_trend_changed(self, trend):
        """
        Closes the open position if the trend has changed.
        Returns True if a position was closed, False otherwise.
        """
        try:
            open_positions = self.data_fetcher.get_open_positions(self.symbol)
            if open_positions:
                current_position = open_positions[0]  # Assume only one open position at a time
                position_side = current_position['side']

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
                    logging.info("Position closed due to trend change.")
                    return True
                else:
                    logging.info(f"No trend change detected. Current position side: {position_side}, trend: {trend}.")
            else:
                logging.info("No open positions to check for trend change.")
            return False
        except Exception as e:
            logging.error(f"Error closing position: {e}")
            return False

    def job(self):
        logging.info("-------------------- Bot Iteration --------------------")

        try:
            m15_data = self.data_fetcher.get_historical_data(self.symbol, '15', 400)
            if not m15_data:
                logging.warning("Failed to fetch data for required timeframes.")
                return

            m15_df = self.strategy.prepare_dataframe(m15_data)
            current_price = self.data_fetcher.get_real_time_price(self.symbol)
            logging.info(f"Real-time price for {self.symbol}: {current_price}")

            trendEMA = self.strategy.ema_trend_strategy(m15_df)
            logging.info(f"15-min Trend EMA: {trendEMA}")

            m15_df['rsi'] = self.indicators.calculate_rsi(m15_df, 14)
            rsi = m15_df['rsi'].iloc[-1]
            logging.info(f"RSI: {rsi}")

            open_positions = self.data_fetcher.get_open_positions(self.symbol)
            if open_positions:
                logging.info("An open position exists. Checking for trend change.")
                if self.close_position_if_trend_changed(trendEMA):
                    logging.info("Position closed due to trend change. Pausing bot for 36 hours.")
                    time.sleep(36 * 60 * 60)  # Sleep for 36 hours
                    return

            if not self.check_last_position_time():
                return

            confirmation_signal = self.strategy.rsi_bollinger_macd_confirmation(m15_df, trendEMA, current_price)
            if confirmation_signal:
                stop_loss, take_profit = self.risk_management.calculate_risk_management(m15_df, confirmation_signal)
                side = 'Buy' if confirmation_signal == 'buy' else 'Sell'

                logging.info(f"Signal confirmed: {confirmation_signal} - Placing {side} order.")
                order_result = self.data_fetcher.place_order(
                    symbol=self.symbol,
                    side=side,
                    qty=self.quantity,
                    current_price=current_price,
                    leverage=10,
                    take_profit=take_profit,
                )

                if order_result:
                    logging.info(f"Order successfully placed: {order_result}")
                else:
                    logging.error("Failed to place order.")
            else:
                logging.info("No trade signal generated.")
        except Exception as e:
            logging.error(f"Error during bot iteration: {e}")

    def run(self):
        self.job()  # Execute once immediately
        schedule.every(10).seconds.do(self.job)

        while not self.stop_bot:
            schedule.run_pending()
            time.sleep(1)


if __name__ == "__main__":
    try:
        bot = TradingBot()
        bot.run()
    except KeyboardInterrupt:
        logging.info("Bot stopped by user.")
