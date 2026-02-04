import os
import threading
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ======================
# Telegram Bot Token
# ======================
BOT_TOKEN = os.environ.get("BOT_TOKEN")

# ======================
# Flask server (for Koyeb health check)
# ======================
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running"

def run_server():
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)

# ======================
# Telegram bot handlers
# ======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("البوت شغال ✅")

def run_bot():
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.run_polling()

# ======================
# Main
# ======================
if __name__ == "__main__":
    threading.Thread(target=run_server).start()
    run_bot()