import os
import websocket
import json
from dotenv import load_dotenv
from stock_notifier.models import WebSocketResponse, WebSocketRequest

load_dotenv()

to_listen = {}


def notify(symbol: str, curr: float, desired: float):
    print(f"ALERT: {symbol} has hit price: {curr} (your desired price: {desired})")


def on_message(ws, message):
    msg = WebSocketResponse(**json.loads(message))
    trades_to_listen = filter(lambda item: item.symbol in to_listen.keys(), msg.data)
    for trade in trades_to_listen:
        prices = to_listen[trade.symbol]
        to_notify = filter(lambda item: trade.last_price >= item, prices)
        for price in to_notify:
            notify(trade.symbol, price)
    print(msg.data[0].last_price)


def on_open(ws):
    # req = WebSocketRequest(type="subscribe", symbol="BINANCE:BTCUSDT")
    ws.send('ping')


if __name__ == "__main__":
    token = os.environ.get("FINNHUB_TOKEN")
    ws = websocket.WebSocketApp(
        f"wss://ws.finnhub.io?token={token}",
        on_message=on_message,
    )
    # ws.
    ws.on_open = on_open

    symb = input("Enter symbol name: ")
    price = input("Enter desired price: ")

    req = WebSocketRequest(type="subscribe", symbol=symb)
    ws.send(req)
    ws.run_forever()
