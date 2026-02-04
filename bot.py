import os
import logging
import requests
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

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
    """
    استدعاء Gemini مع سياق لكل مستخدم.
    mode يحدد نوع المهمة: chat / summarize / rewrite / reply / idea / plan / analyze
    """
    history = user_context.get(user_id, [])

    # نبني توجيه (system style) يخليه مطيع لكن حذر من الأشياء المؤذية
    base_instruction = (
        "أنت مساعد شخصي عربي، مطيع قدر الإمكان، تحاول تنفيذ طلب المستخدم بدون جدال، "
        "وترد باختصار ووضوح، لكن تتجنب أي شيء ضار أو غير قانوني أو مؤذٍ.\n"
    )

    if mode == "summarize":
        task_instruction = "مهمتك الآن: تلخيص النص التالي بشكل واضح ومختصر:\n"
    elif mode == "rewrite":
        task_instruction = "مهمتك الآن: إعادة صياغة النص بأسلوب أفضل وواضح:\n"
    elif mode == "reply":
        task_instruction = (
            "مهمتك الآن: كتابة رد مناسب على الرسالة التالية، بأسلوب محترم ومتزن:\n"
        )
    elif mode == "idea":
        task_instruction = "مهمتك الآن: اقتراح أفكار مفيدة بناءً على طلب المستخدم:\n"
    elif mode == "plan":
        task_instruction = "مهمتك الآن: وضع خطة واضحة من خطوات عملية:\n"
    else:
        task_instruction = "مهمتك الآن: محادثة ذكية ومساعدة المستخدم قدر الإمكان:\n"

    prompt = base_instruction + task_instruction + user_message

    # نحدّث السياق للمحادثة العادية فقط
    if mode == "chat":
        history.append({"role": "user", "content": user_message})
        if len(history) > 10:
            history = history[-10:]
        user_context[user_id] = history

        messages_text = ""
        for msg in history:
            role = msg["role"]
            content = msg["content"]
            messages_text += f"{role.upper()}: {content}\n"

        prompt = base_instruction + "سياق المحادثة:\n" + messages_text + "ASSISTANT:"

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        "gemini-1.5-flash:generateContent"
        f"?key={GEMINI_API_KEY}"
    )
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }

    try:
        resp = requests.post(url, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        text = "صار خطأ وأنا أحاول أكلم نموذج الذكاء، جرّب بعد شوي."

    if mode == "chat":
        history.append({"role": "assistant", "content": text})
        user_context[user_id] = history

    return text


# ===== أوامر البوت =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "هلا، أنا الإيجنت حقك 🌙\n"
        "اكتب لي أي شيء، أو استخدم /help تشوف الأوامر."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "الأوامر المتاحة:\n"
        "/start - بداية المحادثة\n"
        "/help - عرض الأوامر\n"
        "/ping - تتأكد إن البوت صاحي\n"
        "/clear - مسح سياق المحادثة\n"
        "/summarize - تلخيص نص\n"
        "/rewrite - إعادة صياغة نص\n"
        "/reply - كتابة رد لرسالة\n"
        "/idea - اقتراح أفكار\n"
        "/plan - وضع خطة\n"
        "وأي رسالة عادية = محادثة ذكية (Agent)."
    )


async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("البوت شغال ✅")


async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_context.pop(user_id, None)
    await update.message.reply_text("مسحت سياق المحادثة، نبدأ من جديد 🤍")


async def summarize(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = " ".join(context.args) if context.args else ""
    if not text:
        await update.message.reply_text("أرسل الأمر كذا:\n/summarize نص طويل هنا")
        return
    await update.message.chat.send_action(action="typing")
    reply = call_gemini_api(update.effective_user.id, text, mode="summarize")
    await update.message.reply_text(reply)


async def rewrite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = " ".join(context.args) if context.args else ""
    if not text:
        await update.message.reply_text("أرسل الأمر كذا:\n/rewrite النص اللي تبي أعيد صياغته")
        return
    await update.message.chat.send_action(action="typing")
    reply = call_gemini_api(update.effective_user.id, text, mode="rewrite")
    await update.message.reply_text(reply)


async def reply_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = " ".join(context.args) if context.args else ""
    if not text:
        await update.message.reply_text(
            "أرسل الأمر كذا:\n/reply الرسالة اللي تبي أكتب لك رد عليها"
        )
        return
    await update.message.chat.send_action(action="typing")
    reply = call_gemini_api(update.effective_user.id, text, mode="reply")
    await update.message.reply_text(reply)


async def idea(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = " ".join(context.args) if context.args else ""
    if not text:
        await update.message.reply_text("أرسل الأمر كذا:\n/idea الفكرة أو الشي اللي تبي أفكار حوله")
        return
    await update.message.chat.send_action(action="typing")
    reply = call_gemini_api(update.effective_user.id, text, mode="idea")
    await update.message.reply_text(reply)


async def plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = " ".join(context.args) if context.args else ""
    if not text:
        await update.message.reply_text("أرسل الأمر كذا:\n/plan الشي اللي تبي له خطة")
        return
    await update.message.chat.send_action(action="typing")
    reply = call_gemini_api(update.effective_user.id, text, mode="plan")
    await update.message.reply_text(reply)


# ===== الرسائل العادية (الإيجنت) =====
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_text = update.message.text

    await update.message.chat.send_action(action="typing")
    reply = call_gemini_api(user_id, user_text, mode="chat")
    await update.message.reply_text(reply)


# ===== نقطة تشغيل البوت =====
async def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # أوامر
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("ping", ping))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(CommandHandler("summarize", summarize))
    app.add_handler(CommandHandler("rewrite", rewrite))
    app.add_handler(CommandHandler("reply", reply_cmd))
    app.add_handler(CommandHandler("idea", idea))
    app.add_handler(CommandHandler("plan", plan))

    # أي رسالة نصية → تروح للإيجنت
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot is starting...")
    await app.run_polling()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
