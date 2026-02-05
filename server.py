from flask import Flask
import threading
import bot  # يستورد ملف البوت الأصلي

app = Flask(__name__)

@app.route("/")
def home():
    return "OK"

def run_bot():
    bot.main()  # يشغّل البوت من bot.py

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    app.run(host="0.0.0.0", port=8080)
