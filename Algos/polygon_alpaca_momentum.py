from datetime import datetime, timedelta
from dotenv import load_dotenv
from polygon import RESTClient as PolygonClient
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
import os
import time

load_dotenv()

# Initialize clients
polygon_api_key = os.getenv("POLYGON_APIKEY_MEMBER")
alpaca_api_key = os.getenv("ALPACA_APIKEY")
alpaca_secret_key = os.getenv("ALPACA_APIKEY_SECRET")
polygon_client = PolygonClient(polygon_api_key)
alpaca_client = TradingClient(alpaca_api_key, alpaca_secret_key, paper=True)

# Parameters
STOCK_UNIVERSE = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
LOOKBACK_PERIOD = 20
BUY_THRESHOLD = 0.05
SELL_THRESHOLD = -0.05
TRADE_QUANTITY = 10
START_CAPITAL = 100000

# ---- Data Fetching ----
def fetch_full_historical_data(symbol, start_date, end_date):
    bars = polygon_client.get_aggs(symbol, 1, "day", start_date, end_date)
    return {datetime.fromtimestamp(bar.timestamp / 1000).date(): bar.close for bar in bars}

def fetch_live_price(symbol):
    last_trade = polygon_client.get_last_trade(symbol)
    return last_trade.price

def fetch_intraday_data(symbol, interval="minute", limit=20):
    """Fetches recent intraday data for live momentum calculation."""
    bars = polygon_client.get_aggs(symbol, 15, interval, limit=limit)
    return [bar.close for bar in bars]

# ---- Momentum Calculation ----
# def calculate_momentum(prices, current_date):
#     trading_dates = sorted([date for date in prices.keys() if date < current_date])
#     if len(trading_dates) < LOOKBACK_PERIOD:
#         return None
    
#     lookback_start_date = trading_dates[-LOOKBACK_PERIOD]
#     lookback_prices = [prices[date] for date in trading_dates if lookback_start_date <= date < current_date]
#     if len(lookback_prices) < LOOKBACK_PERIOD:
#         return None
    
#     return (lookback_prices[-1] - lookback_prices[0]) / lookback_prices[0]
def calculate_momentum(prices, current_date, live_mode=False):
    if live_mode:
        # Use intraday prices in live mode
        if len(prices) < LOOKBACK_PERIOD:
            return None  # Not enough data for intraday momentum
        return (prices[-1] - prices[0]) / prices[0]
    else:
        # Use daily prices in backtesting mode
        trading_dates = sorted([date for date in prices.keys() if date < current_date])
        if len(trading_dates) < LOOKBACK_PERIOD:
            return None

        lookback_start_date = trading_dates[-LOOKBACK_PERIOD]
        lookback_prices = [prices[date] for date in trading_dates if lookback_start_date <= date < current_date]
        if len(lookback_prices) < LOOKBACK_PERIOD:
            return None

        return (lookback_prices[-1] - lookback_prices[0]) / lookback_prices[0]

# ---- Signal Generation ----
# def generate_signals(stock_data, current_date, live_mode=False):
#     signals = {}
#     for symbol, prices in stock_data.items():
#         if not live_mode and current_date not in prices:
#             continue
#         momentum = calculate_momentum(prices, current_date)
#         if momentum is not None:
#             if momentum > BUY_THRESHOLD:
#                 signals[symbol] = OrderSide.BUY
#             elif momentum < SELL_THRESHOLD:
#                 signals[symbol] = OrderSide.SELL
#     return signals
def generate_signals(stock_data, current_date, live_mode=False):
    signals = {}
    for symbol, prices in stock_data.items():
        if not live_mode and current_date not in prices:
            continue
        momentum = calculate_momentum(prices, current_date, live_mode=live_mode)
        if momentum is not None:
            if momentum > BUY_THRESHOLD:
                signals[symbol] = OrderSide.BUY
            elif momentum < SELL_THRESHOLD:
                signals[symbol] = OrderSide.SELL
        else:
            print(f"No signal for symbol: {symbol}")
    return signals

# ---- Trade Execution ----
def execute_trade(symbol, side, price=None, live_mode=False):
    if live_mode:
        # Place a live trade with Alpaca
        order_data = MarketOrderRequest(
            symbol=symbol,
            qty=TRADE_QUANTITY,
            side=side,
            time_in_force=TimeInForce.DAY
        )
        alpaca_client.submit_order(order_data)
        print(f"Live order placed: {side} {TRADE_QUANTITY} shares of {symbol}")
    else:
        # In backtest, simply track the transaction
        print(f"Backtest trade: {side} {TRADE_QUANTITY} shares of {symbol} at price {price}")

# ---- Backtest Strategy ----
def backtest_strategy():
    portfolio_value = START_CAPITAL  
    positions = {symbol: 0 for symbol in STOCK_UNIVERSE}
    stock_data = {symbol: fetch_full_historical_data(symbol, START_DATE, END_DATE) for symbol in STOCK_UNIVERSE}
    
    for current_date in sorted(stock_data[STOCK_UNIVERSE[0]].keys()):
        signals = generate_signals(stock_data, current_date)
        for symbol, action in signals.items():
            price = stock_data[symbol].get(current_date)
            if action == OrderSide.BUY and portfolio_value > 0:
                shares_to_buy = portfolio_value * 0.1 // price
                portfolio_value -= shares_to_buy * price
                positions[symbol] += shares_to_buy
                print(f"Backtest bought {shares_to_buy} shares of {symbol} at {price} on {current_date}")

            elif action == OrderSide.SELL and positions[symbol] > 0:
                portfolio_value += positions[symbol] * price
                print(f"Backtest sold {positions[symbol]} shares of {symbol} at {price} on {current_date}")
                positions[symbol] = 0

    print("Backtest complete")
    print("Final portfolio value:", portfolio_value)
    print("Final positions:", positions)

# ---- Live Trading Strategy ----
def live_trading_strategy():
    while True:
        stock_data = {}
        for symbol in STOCK_UNIVERSE:
            historical_data = fetch_full_historical_data(symbol, datetime.now() - timedelta(days=LOOKBACK_PERIOD + 5), datetime.now())
            stock_data[symbol] = historical_data

        signals = generate_signals(stock_data, datetime.now().date(), live_mode=True)

        for symbol, action in signals.items():
            price = fetch_live_price(symbol)
            execute_trade(symbol, action, price, live_mode=True)

        print("Waiting for the next trading interval...")
        time.sleep(60 * 1)  # Run every 15 minutes

# ---- Run Strategy ----
if __name__ == "__main__":
    START_DATE = datetime(2018, 1, 1)
    END_DATE = datetime(2024, 11, 23)
    # backtest_strategy()  # Run backtest

    # Uncomment the line below to start live trading
    live_trading_strategy()
