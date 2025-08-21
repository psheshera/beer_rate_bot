import os
from collections import defaultdict
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

DATA_FILE = "/mnt/data/ratings.txt"
user_states = {}

def capitalize(text):
    return text[:1].upper() + text[1:].lower()

async def bar_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Введите название бара:")
    user_states[update.effective_user.id] = {"step": "bar"}

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    if user_id not in user_states:
        await update.message.reply_text("Введите /bar для начала.")
        return

    state = user_states[user_id]

    if state["step"] == "bar":
        state["bar"] = text.lower()
        state["step"] = "beer"
        await update.message.reply_text("Введите название пива:")
    elif state["step"] == "beer":
        state["beer"] = text.lower()
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
        user = update.effective_user.username or update.effective_user.first_name or "unknown"

        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
        with open(DATA_FILE, "a") as f:
            f.write(f"{bar};{beer};{score};{user}\n")

        await update.message.reply_text(
            f"Оценка сохранена! Бар: {capitalize(bar)}, Пиво: {capitalize(beer)}, Оценка: {score}, Пользователь: {user}"
        )
        state["step"] = "beer"
        await update.message.reply_text("Введите название следующего пива или /bar для нового бара.")

async def summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not os.path.exists(DATA_FILE):
        await update.message.reply_text("Нет данных для отображения.")
        return

    ratings = defaultdict(lambda: defaultdict(list))
    user_scores = defaultdict(list)

    with open(DATA_FILE, "r") as f:
        for line in f:
            try:
                bar, beer, score, user = line.strip().split(";")
                score = int(score)
                ratings[bar][beer].append(score)
                user_scores[user].append(score)
            except ValueError:
                continue

    if not ratings:
        await update.message.reply_text("Нет данных для отображения.")
        return

    response = "📊 Сводка по барам и пиву:\n"
    for bar, beers in ratings.items():
        response += f"\n🍺 Бар: {capitalize(bar)}\n"
        for beer, scores in beers.items():
            avg = sum(scores) / len(scores)
            response += f"  - {capitalize(beer)}: {avg:.2f} (оценок: {len(scores)})\n"

    best_user = None
    best_avg = -1
    for user, scores in user_scores.items():
        avg = sum(scores) / len(scores)
        if avg > best_avg:
            best_avg = avg
            best_user = user

    if best_user:
        response += f"\n🏆 Пользователь с самой высокой средней оценкой: {best_user} ({best_avg:.2f})"

    await update.message.reply_text(response)

async def zerorating(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
        with open(DATA_FILE, "w") as f:
            f.write("")
        await update.message.reply_text("Файл с рейтингами очищен.")
    except Exception as e:
        await update.message.reply_text(f"Ошибка при очистке файла: {e}")

if __name__ == "__main__":
    app = ApplicationBuilder().token(os.getenv("TELEGRAM_TOKEN")).build()
    app.add_handler(CommandHandler("bar", bar_command))
    app.add_handler(CommandHandler("summary", summary))
    app.add_handler(CommandHandler("zerorating", zerorating))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()
