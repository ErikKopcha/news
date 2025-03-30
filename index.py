import os
import json
import openai
import logging
from datetime import datetime
from telegram import Bot
from telegram.ext import Application, CommandHandler

# --- Load ENV ---
from dotenv import load_dotenv
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

HISTORY_FILE = "news_history.json"

PROMPT_TEMPLATE = """
Щодня надавай мені коротку, стислу сводку найважливіших новин за останню добу.
Мене цікавлять теми:
- криптовалюти та інвестиції
- технології (AI, hardware, великі компанії)
- програмування (React, Next.js, JavaScript)
- стихійні лиха, катастрофи
- головні новини України та світу

Уникай повторів. Враховуй історію попередніх зведень. Видавай тільки найрелевантніше, у форматі:

1. Заголовок новини — короткий опис
2. ...

Якщо є щось дуже важливе — познач **[важливо]**.
"""

# --- Load news history ---
def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, "r") as f:
        return json.load(f)

# --- Save history ---
def save_history(news_list):
    with open(HISTORY_FILE, "w") as f:
        json.dump(news_list, f)

# --- Generate news summary ---
def get_news_summary():
    history = load_history()
    prompt = PROMPT_TEMPLATE + f"\nОсь попередні новини: {history[-5:]}"

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Ти аналітик новин."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=800,
        temperature=0.7
    )

    news = response.choices[0].message.content.strip()
    history.append({"date": datetime.now().isoformat(), "news": news})
    save_history(history)
    return news

# --- Telegram send function ---
def send_news(context=None):
    bot = Bot(token=TELEGRAM_TOKEN)
    news = get_news_summary()
    bot.send_message(chat_id=CHAT_ID, text=news)

# --- For manual command (optional) ---
async def news_command(update, context):
    news = get_news_summary()
    await update.message.reply_text(news)

# --- Main bot loop (for deployment) ---
def main():
    logging.basicConfig(level=logging.INFO)
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("news", news_command))
    application.run_polling()

if __name__ == "__main__":
    main()
