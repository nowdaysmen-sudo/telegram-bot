import os
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import CommandHandler, Application

BOT_TOKEN = os.environ.get("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
app = Flask(__name__)

application = Application.builder().bot(bot).build()

async def start(update: Update, context):
    await update.message.reply_text("البوت شغال ✅")

application.add_handler(CommandHandler("start", start))


@app.route("/", methods=["POST"])
async def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    await application.process_update(update)
    return "ok"


@app.route("/", methods=["GET"])
def index():
    return "Bot is running"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)