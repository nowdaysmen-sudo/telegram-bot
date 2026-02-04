from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from flask import Flask
import threading
import os

BOT_TOKEN = os.environ.get("BOT_TOKEN")

app = Flask(__name__)

@app.route("/")
def home():
    return "OK"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("البوت شغال")

def run_bot():
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.run_polling()

def run_server():
    app.run(host="0.0.0.0", port=8000)

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    run_server()