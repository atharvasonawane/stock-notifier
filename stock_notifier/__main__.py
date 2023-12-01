import os
import asyncio
from threading import Thread, Lock
from typing import Dict, Tuple

import json
from websocket import WebSocketApp
from dotenv import load_dotenv

from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, Application

from stock_notifier.models import WebSocketResponse, WebSocketRequest


TG_APP: Application
SOCKET: WebSocketApp
LOCK = Lock()
SUBSCRIPTIONS: Dict[str, Tuple[str, float]] = {}


def on_message(ws, message):
    try:
        with LOCK:
            msg = WebSocketResponse(**json.loads(message))
            trades_to_listen = filter(
                lambda item: item.symbol in SUBSCRIPTIONS.keys(), msg.data
            )
            for trade in trades_to_listen:
                subs = SUBSCRIPTIONS[trade.symbol]
                for sub in subs:
                    if trade.last_price >= sub[1]:
                        asyncio.run(
                            TG_APP.bot.send_message(
                                chat_id=sub[0],
                                text=f"""
📢 Price Alert!
**{trade.symbol}** is now at **{trade.last_price}**! ()
""",
                            )
                        )
                    SUBSCRIPTIONS[trade.symbol].remove(sub)

    except Exception as e:
        print(f"Message: {message}")
        print(f"Exception: {e}")


def start_websocket():
    token = os.environ.get("FINNHUB_TOKEN")
    global SOCKET
    SOCKET = WebSocketApp(f"wss://ws.finnhub.io?token={token}", on_message=on_message)
    SOCKET.run_forever()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="""
📈 Welcome to Stock Notifier Bot! 🔔

To subscribe to a stock, use the following format:
`/subscribe {stock-symbol} {trigger-price}`

For example:
`/subscribe AAPL 120`
""",
    )


async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    split = update.message.text.split(" ")
    if len(split) != 3:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="""
‼️ Error: invalid format. 

Please use the following format:
`/subscribe {stock-symbol} {trigger-price}`

For example:
`/subscribe AAPL 120`
""",
        )
        return

    symbol = split[1]
    trigger = float(split[2])
    if symbol not in SUBSCRIPTIONS.keys():
        SUBSCRIPTIONS[symbol] = [(update.effective_chat.id, trigger)]
        req = WebSocketRequest(type="subscribe", symbol=symbol)
        SOCKET.send(req.model_dump_json())
    else:
        SUBSCRIPTIONS[symbol].append((update.effective_chat.id, trigger))
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"""
✅ Subscription successful!
You will be notified when **{symbol}** hits **{trigger}** or heigher.
""",
    )


def start_bot():
    global TG_APP
    TG_APP = ApplicationBuilder().token(os.environ.get("TELEGRAM_API_TOKEN")).build()

    start_handler = CommandHandler("start", start)
    subscribe_handler = CommandHandler("subscribe", subscribe)

    TG_APP.add_handler(start_handler)
    TG_APP.add_handler(subscribe_handler)
    TG_APP.run_polling()


if __name__ == "__main__":
    load_dotenv()
    ws_thread = Thread(target=start_websocket)
    ws_thread.start()
    start_bot()
    ws_thread.join()
