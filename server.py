#!/usr/bin/env python
# Telegram Bot with Groq API integration
# Based on python-telegram-bot official example

import asyncio
import logging
import os
from http import HTTPStatus

import requests
import uvicorn
from asgiref.wsgi import WsgiToAsgi
from flask import Flask, Response, make_response, request

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# Configuration from environment variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://healthy-vitia-qht-5e46f5a9.koyeb.app")
PORT = 8000

if not TELEGRAM_TOKEN:
    raise RuntimeError("TELEGRAM_TOKEN is not set in environment variables.")
if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY is not set in environment variables.")


def call_groq_api(prompt: str) -> str:
    """Call Groq API and return the response."""
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 1024
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error(f"Groq API error: {e}")
        return "عذراً، حدث خطأ. حاول مرة أخرى."


async def start(update: Update, context) -> None:
    """Handle /start command."""
    await update.message.reply_text(
        "مرحباً! أنا بوت ذكي يستخدم Groq AI.\n"
        "أرسل لي أي رسالة وسأرد عليك! 🤖"
    )


async def handle_message(update: Update, context) -> None:
    """Handle incoming messages."""
    user_message = update.message.text
    logger.info(f"Received message: {user_message}")
    
    # Call Groq API
    response = call_groq_api(user_message)
    
    # Send response
    await update.message.reply_text(response)


async def main() -> None:
    """Set up PTB application and web server."""
    # Create application
    application = (
        Application.builder()
        .token(TELEGRAM_TOKEN)
        .updater(None)  # We handle updates manually via webhook
        .build()
    )

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Set webhook
    await application.bot.set_webhook(url=f"{WEBHOOK_URL}/webhook", allowed_updates=Update.ALL_TYPES)
    logger.info(f"Webhook set to: {WEBHOOK_URL}/webhook")

    # Set up Flask webserver
    flask_app = Flask(__name__)

    @flask_app.post("/webhook")
    async def webhook() -> Response:
        """Handle incoming Telegram updates."""
        await application.update_queue.put(
            Update.de_json(data=request.json, bot=application.bot)
        )
        return Response(status=HTTPStatus.OK)

    @flask_app.get("/")
    async def health() -> Response:
        """Health check endpoint."""
        response = make_response("Bot is running! 🤖", HTTPStatus.OK)
        response.mimetype = "text/plain"
        return response

    # Configure uvicorn server
    webserver = uvicorn.Server(
        config=uvicorn.Config(
            app=WsgiToAsgi(flask_app),
            port=PORT,
            use_colors=False,
            host="0.0.0.0",  # Listen on all interfaces for Koyeb
        )
    )

    # Run application and webserver together
    async with application:
        await application.start()
        logger.info(f"Starting Flask server on port {PORT}...")
        await webserver.serve()
        await application.stop()


if __name__ == "__main__":
    asyncio.run(main())
