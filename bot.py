import os
import threading
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from openai import OpenAI

# ENV
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY topilmadi")

client = OpenAI()

memory = [
    {"role": "system", "content": "Sen faqat o‘zbek tilida gapiradigan aqlli yordamchisan."}
]

# Flask (PORT uchun)
web = Flask(__name__)

@web.route("/")
def home():
    return "Bot ishlayapti 🚀"

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ Bu bot yopiq.")
        return

    user_text = update.message.text
    memory.append({"role": "user", "content": user_text})

    try:
        response = client.responses.create(
            model="gpt-4.1-mini",
            input=memory
        )

        answer = response.output_text
        memory.append({"role": "assistant", "content": answer})

if len(memory) > 30:
    memory[:] = memory[-30:]

        await update.message.reply_text(answer)

    except Exception as e:
        await update.message.reply_text("❌ Xatolik yuz berdi.")
        print("OpenAI error:", e)

def run_bot():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    app.run_polling()

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    web.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
