import os
import threading
from http.server import SimpleHTTPRequestHandler, HTTPServer
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

# -----------------------------
# 1) تشغيل سيرفر وهمي لـ Koyeb
# -----------------------------
def run_server():
    server = HTTPServer(("0.0.0.0", 8000), SimpleHTTPRequestHandler)
    server.serve_forever()

threading.Thread(target=run_server, daemon=True).start()

# -----------------------------
# 2) قراءة التوكن من
