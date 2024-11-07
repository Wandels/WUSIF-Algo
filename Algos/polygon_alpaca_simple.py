from polygon import RESTClient
import os
from polygon import RESTClient as PolygonClient
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from dotenv import load_dotenv

load_dotenv()
polygon_api_key = os.getenv("POLYGON_APIKEY_MEMBER")
alpaca_api_key = os.getenv("ALPACA_APIKEY")
alpaca_secret_key = os.getenv("ALPACA_APIKEY_SECRET")
alpaca_base_url = os.getenv("ALPACA_API_BASE_URL")


polygon_client = RESTClient(api_key=polygon_api_key)
#alpaca_client = TradingClient(os.getenv("APCA_API_KEY_ID"), os.getenv("APCA_API_SECRET_KEY"), paper=True)
alpaca_client = TradingClient(alpaca_api_key, alpaca_secret_key, paper=True)

symbol = "AAPL"


def get_latest_price(symbol):
    last_trade = polygon_client.get_last_trade(symbol)
    return last_trade.price

# Function to place a trade
def place_trade(side, qty):
    order_data = MarketOrderRequest(
        symbol=symbol,
        qty=qty,
        side=side,
        time_in_force=TimeInForce.DAY
    )
    alpaca_client.submit_order(order_data)
    print(f"Order placed: {side} {qty} shares of {symbol}")

# Simple trading strategy: Buy if price < 100, sell if price > 150
def trading_strategy():
    price = get_latest_price(symbol)
    print(f"Latest price for {symbol}: ${price}")

    if price < 100:
        place_trade(OrderSide.BUY, 1)
    elif price > 150:
        place_trade(OrderSide.SELL, 1)
    else:
        print("No trade placed. Waiting for the next opportunity.")

# Run the strategy
if __name__ == "__main__":
    trading_strategy()