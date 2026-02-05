from flask import Flask
import threading
import asyncio
import bot  # يستورد ملف البوت الأصلي

app = Flask(__name__)

@app.route("/")
def home():
    return "OK"

def run_bot():
    # إنشاء event loop جديد للـ thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # تشغيل البوت
    bot.main()

if __name__ == "__main__":
    # تشغيل البوت في thread منفصل
    threading.Thread(target=run_bot, daemon=True).start()
    
    # تشغيل Flask على port 8000 (مش 8080)
    app.run(host="0.0.0.0", port=8000)
