import os
import logging
import requests
import threading
from http.server import SimpleHTTPRequestHandler, HTTPServer
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ----------------------------------------
# 1) تشغيل سيرفر وهمي لـ Koyeb على المنفذ 8000
# ----------------------------------------
def run_server():
    server = HTTPServer(("0.0.0.0", 8000), SimpleHTTPRequestHandler)
    server.serve_forever()

threading.Thread(target=run_server, daemon=True).start()

# ===== إعداد اللوق =====
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ===== مفاتيح من Environment Variables =====
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not TELEGRAM_TOKEN:
    raise RuntimeError("TELEGRAM_TOKEN is not set in environment variables.")
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY is not set in environment variables.")

# ===== ذاكرة بسيطة لكل مستخدم =====
user_context = {}  # user_id -> list of messages


def call_gemini_api(user_id: int, user_message: str, mode: str = "chat") -> str:
    history = user_context.get(user_id, [])

    base_instruction = (
        "أنت مساعد شخصي عربي، مطيع قدر الإمكان، تحاول تنفيذ طلب المستخدم بدون جدال، "
        "وترد باختصار ووضوح، لكن تتجنب أي شيء ضار أو غير قانوني أو مؤذٍ.\n"
    )

    if mode == "summarize":
        task_instruction = "مهمتك الآن: تلخيص النص التالي:\n"
    elif mode == "rewrite":
        task_instruction = "مهمتك الآن: إعادة صياغة النص:\n"
    elif mode == "reply":
        task_instruction = "مهمتك الآن: كتابة رد مناسب:\n"
    elif mode == "idea":
        task_instruction = "مهمتك الآن: اقتراح أفكار:\n"
    elif mode == "plan":
        task_instruction = "مهمتك الآن: وضع خطة:\n"
    else:
        task_instruction = "محادثة ذكية:\n"

    prompt = base_instruction + task_instruction + user_message

    if mode == "chat":
        history.append({"role": "user", "content": user_message})
        if len(history) > 10:
            history = history[-10:]
        user_context[user_id] = history

        messages_text = ""
        for msg in history:
            messages_text += f"{msg['role'].upper()}: {msg['content']}\n"

        prompt = base_instruction + "سياق المحادثة:\n" + messages_text + "ASSISTANT:"

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        "gemini-1.5-flash:generateContent"
        f"?key={GEMINI_API_KEY}"
    )
    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    try:
        resp = requests.post(url, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        text = "صار خطأ، جرّب بعد شوي."

    if mode == "chat":
        history.append({"role": "assistant", "content": text})
        user_context[user_id] = history

    return text


# ===== أوامر البوت =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("هلا، أنا الإيجنت حقك 🌙")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/start\n/help\n/ping\n/clear\n/summarize\n/rewrite\n/reply\n/idea\n/plan"
    )


async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("البوت شغال ✅")


async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_context.pop(update.effective_user.id, None)
    await update.message.reply_text("تم مسح السياق 🤍")


async def summarize(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = " ".join(context.args)
    if not text:
        return await update.message.reply_text("استخدم:\n/summarize نص")
    reply = call_gemini_api(update.effective_user.id, text, "summarize")
    await update.message.reply_text(reply)


async def rewrite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = " ".join(context.args)
    if not text:
        return await update.message.reply_text("استخدم:\n/rewrite نص")
    reply = call_gemini_api(update.effective_user.id, text, "rewrite")
    await update.message.reply_text(reply)


async def reply_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = " ".join(context.args)
    if not text:
        return await update.message.reply_text("استخدم:\n/reply نص")
    reply = call_gemini_api(update.effective_user.id, text, "reply")
    await update.message.reply_text(reply)


async def idea(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = " ".join(context.args)
    if not text:
        return await update.message.reply_text("استخدم:\n/idea نص")
    reply = call_gemini_api(update.effective_user.id, text, "idea")
    await update.message.reply_text(reply)


async def plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = " ".join(context.args)
    if not text:
        return await update.message.reply_text("استخدم:\n/plan نص")
    reply = call_gemini_api(update.effective_user.id, text, "plan")
    await update.message.reply_text(reply)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply = call_gemini_api(update.effective_user.id, update.message.text, "chat")
    await update.message.reply_text(reply)


# ===== تشغيل Webhook =====
async def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("ping", ping))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(CommandHandler("summarize", summarize))
    app.add_handler(CommandHandler("rewrite", rewrite))
    app.add_handler(CommandHandler("reply", reply_cmd))
    app.add_handler(CommandHandler("idea", idea))
    app.add_handler(CommandHandler("plan", plan))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    await app.initialize()
    await app.start()

    # 🔥 هنا الويب هوك الجديد الصحيح
    await app.bot.set_webhook(
        url="https://healthy-vitia-qht-5e46f5a9.koyeb.app/"
    )

    await app.run_webhook(
        listen="0.0.0.0",
        port=8000,
        url_path="",
    )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
