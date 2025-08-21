import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

DATA_FILE = "/mnt/data/ratings.txt"  # путь к файлу на Railway volume

user_states = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Введите название бара:")
    user_states[update.effective_user.id] = {"step": "bar"}

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if user_id not in user_states:
        await update.message.reply_text("Введите /start для начала.")
        return

    state = user_states[user_id]

    if state["step"] == "bar":
        state["bar"] = text
        state["step"] = "beer"
        await update.message.reply_text("Введите название пива:")
    elif state["step"] == "beer":
        state["beer"] = text
        state["step"] = "score"
        await update.message.reply_text("Введите оценку от 1 до 10:")
    elif state["step"] == "score":
        try:
            score = int(text)
            if not (1 <= score <= 10):
                raise ValueError
        except ValueError:
            await update.message.reply_text("Ошибка: нужно ввести число от 1 до 10.")
            return

        bar = state["bar"]
        beer = state["beer"]

        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
        with open(DATA_FILE, "a") as f:
            f.write(f"{bar};{beer};{score}\n")

        await update.message.reply_text(f"Оценка сохранена! Бар: {bar}, Пиво: {beer}, Оценка: {score}")
        state["step"] = "beer"
        await update.message.reply_text("Введите название следующего пива или /start для нового бара.")

app = ApplicationBuilder().token(os.getenv("TELEGRAM_TOKEN")).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

app.run_polling()
