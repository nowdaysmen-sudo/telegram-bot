import os
import threading
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ====== Telegram token ======
BOT_TOKEN = os.environ.get("BOT_TOKEN")

# ====== Flask app (health check فقط) ======
app = Flask(__name__)

@app.route("/")
def home():
    return "OK", 200

def run_flask():
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)

# ====== Telegram bot ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("البوت شغال ✅")

async def run_bot():
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    await application.run_polling()

# ====== Main ======
if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    import asyncio
    asyncio.run(run_bot())