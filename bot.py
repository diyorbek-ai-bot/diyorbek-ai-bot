import os
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from openai import OpenAI

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OWNER_ID = int(os.getenv("OWNER_ID"))

client = OpenAI(api_key=OPENAI_API_KEY)
memory = []

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ Bu bot yopiq.")
        return

    user_text = update.message.text
    memory.append({"role": "user", "content": user_text})

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Sen faqat o‘zbek tilida gapiradigan aqlli yordamchisan."},
            *memory
        ]
    )

    answer = response.choices[0].message.content
    memory.append({"role": "assistant", "content": answer})

    await update.message.reply_text(answer)

app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
app.run_polling()
