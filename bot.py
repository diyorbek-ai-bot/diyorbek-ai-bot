import os
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import (
    Application,
    ApplicationBuilder,
    MessageHandler,
    ContextTypes,
    filters,
)
from openai import OpenAI
import asyncio

# ================== ENV ==================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))
PORT = int(os.getenv("PORT", "10000"))

if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN topilmadi")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY topilmadi")
if OWNER_ID == 0:
    raise ValueError("OWNER_ID noto‘g‘ri")

# ================== OPENAI ==================
client = OpenAI(api_key=OPENAI_API_KEY)

# ================== MEMORY (user-based) ==================
user_memory: dict[int, list] = {}

SYSTEM_PROMPT = {
    "role": "system",
    "content": "Sen faqat o‘zbek tilida gapiradigan aqlli yordamchisan."
}

MAX_HISTORY = 20

# ================== TELEGRAM APP ==================
app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
bot = Bot(token=TELEGRAM_TOKEN)

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user or user.id != OWNER_ID:
        await update.message.reply_text("❌ Bu bot yopiq.")
        return

    text = update.message.text.strip()
    uid = user.id

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

        # xotirani cheklash
        if len(user_memory[uid]) > MAX_HISTORY:
            user_memory[uid] = [SYSTEM_PROMPT] + user_memory[uid][-MAX_HISTORY:]

        await update.message.reply_text(answer)

    except Exception:
        await update.message.reply_text("❌ Xatolik yuz berdi.")

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

# ================== FLASK (WEBHOOK) ==================
web = Flask(__name__)

@web.route("/", methods=["GET"])
def home():
    return "Bot ishlayapti ✅"

@web.route("/webhook", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    asyncio.get_event_loop().create_task(app.process_update(update))
    return "ok"

# ================== START ==================
async def main():
    await app.initialize()
    await bot.set_webhook(
        url=os.getenv("RENDER_EXTERNAL_URL") + "/webhook"
    )
    await app.start()

if __name__ == "__main__":
    asyncio.get_event_loop().create_task(main())
    web.run(host="0.0.0.0", port=PORT)
