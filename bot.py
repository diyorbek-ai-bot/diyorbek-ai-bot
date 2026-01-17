import os
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from openai import OpenAI

# ENV
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))  # crash bo‘lmasin

# OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# oddiy xotira
memory = [
    {"role": "system", "content": "Sen faqat o‘zbek tilida gapiradigan aqlli yordamchisan."}
]

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

        await update.message.reply_text(answer)

    except Exception as e:
        await update.message.reply_text("❌ Xatolik yuz berdi.")
        print("OpenAI error:", e)

# App
app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

print("🤖 Bot ishga tushdi...")
app.run_polling()
