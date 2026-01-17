import os
import threading
from flask import Flask
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    ContextTypes,
    filters,
)
from openai import OpenAI

# ================= ENV =================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))
PORT = int(os.getenv("PORT", "10000"))

if not TELEGRAM_TOKEN:
    raise RuntimeError("TELEGRAM_TOKEN yo‘q")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY yo‘q")
if OWNER_ID == 0:
    raise RuntimeError("OWNER_ID noto‘g‘ri")

# ================= OPENAI =================
client = OpenAI(api_key=OPENAI_API_KEY)

# ================= MEMORY =================
SYSTEM_PROMPT = {
    "role": "system",
    "content": "Sen faqat o‘zbek tilida gapiradigan aqlli yordamchisan."
}
user_memory = {}
MAX_HISTORY = 20

# ================= TELEGRAM =================
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user or user.id != OWNER_ID:
        await update.message.reply_text("❌ Bu bot yopiq.")
        return

    uid = user.id
    text = update.message.text.strip()

    if uid not in user_memory:
        user_memory[uid] = [SYSTEM_PROMPT]

    user_memory[uid].append({"role": "user", "content": text})

    try:
        response = client.responses.create(
            model="gpt-4.1-mini",
            input=user_memory[uid],
        )

        answer = response.output_text.strip()
        user_memory[uid].append({"role": "assistant", "content": answer})

        if len(user_memory[uid]) > MAX_HISTORY:
            user_memory[uid] = [SYSTEM_PROMPT] + user_memory[uid][-MAX_HISTORY:]

        await update.message.reply_text(answer)

    except Exception as e:
        print("OpenAI error:", e)
        await update.message.reply_text("❌ Xatolik yuz berdi.")

def run_bot():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    app.run_polling()

# ================= FLASK (Render uchun) =================
web = Flask(__name__)

@web.route("/")
def home():
    return "Bot ishlayapti ✅"

# ================= START =================
if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    web.run(host="0.0.0.0", port=PORT)
