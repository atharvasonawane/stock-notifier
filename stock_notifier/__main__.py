import os
import asyncio

import json
import websockets
from dotenv import load_dotenv

from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

from stock_notifier.models import WebSocketResponse, WebSocketRequest

load_dotenv()

to_listen = {}


def notify(symbol: str, curr: float, desired: float):
    print(f"ALERT: {symbol} has hit price: {curr} (your desired price: {desired})")


def on_message(ws, message):
    try:
        msg = WebSocketResponse(**json.loads(message))
        trades_to_listen = filter(
            lambda item: item.symbol in to_listen.keys(), msg.data
        )
        for trade in trades_to_listen:
            prices = to_listen[trade.symbol]
            to_notify = filter(lambda item: trade.last_price >= item, prices)
            for price in to_notify:
                notify(trade.symbol, trade.last_price, price)
    except Exception as e:
        print(f"Message: {message}")
        print(f"Exception: {e}")


async def websocket():
    token = os.environ.get("FINNHUB_TOKEN")
    async with websockets.connect(f"wss://ws.finnhub.io?token={token}") as ws:
        symb = input("Enter symbol name: ")
        threshold = float(input("Enter threshold price: "))
        to_listen[symb] = [threshold]
        req = WebSocketRequest(type="subscribe", symbol=symb)
        await ws.send(req.model_dump_json())
        while True:
            on_message(ws, await ws.recv())

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")


async def start_bot():
    token = os.environ.get("TELEGRAM_API_TOKEN")
    application = ApplicationBuilder().token(token).build()

    start_handler = CommandHandler("start", start)
    application.add_handler(start_handler)

    application.run_polling()


if __name__ == "__main__":
    asyncio.run(websocket())
