import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    CallbackQueryHandler,
)
from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage
import pytube
import requests

# Конфигурация
MISTRAL_API_KEY = "1VT63Fiqxn6DwEZXlI5sTGsTSmiNOW5h"
TELEGRAM_TOKEN = "7639504664:AAGCjOPO_euHeAknPN3x8llCYFxv65E8RC0"
BOT_USERNAME = "@minebineldai_bot"  # Например, @mistral_gpt_bot

# Настройки личности бота
BOT_PERSONALITY = """
Ты дружелюбный и уважительный. Отвечай кратко, но информативно. 
Не пиши длинные сообщения. Будь вежливым.
"""

# Клиент Mistral
mistral_client = MistralClient(api_key=MISTRAL_API_KEY)

# Канал, группа и другой бот (по желанию)
CHANNEL_LINK = "https://t.me/minebineld"
GROUP_LINK = "https://t.me/minebineldchat"
OTHER_BOT_LINK = "https://t.me/minebineldbot"

# ===== ОСНОВНЫЕ ФУНКЦИИ ===== #
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я твой ИИ-помощник. Напиши мне что-нибудь!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_type = update.message.chat.type  # private или group
    text = update.message.text

    # Игнорируем сообщения без упоминания в группах
    if message_type == "group" or message_type == "supergroup":
        if BOT_USERNAME.lower() not in text.lower():
            return

    # Убираем упоминание, если это группа
    if message_type != "private":
        text = text.replace(BOT_USERNAME, "").strip()

    # Статус "печатает"
    await update.message.chat.send_action(action="typing")

    # Запрос к Mistral API
    response = mistral_client.chat(
        model="mistral-small-latest",
        messages=[ChatMessage(role="user", content=BOT_PERSONALITY + "\n\n" + text)],
    )

    bot_reply = response.choices[0].message.content
    await update.message.reply_text(bot_reply)

async def send_music(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args)
    if not query:
        await update.message.reply_text("Укажите название музыки, например: /music Coldplay - Yellow")
        return

    await update.message.chat.send_action(action="typing")
    
    try:
        yt = pytube.Search(query).results[0]
        audio_url = yt.streams.filter(only_audio=True).first().url
        
        await update.message.reply_audio(audio_url, title=yt.title)
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")

async def send_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📢 Канал", url=CHANNEL_LINK)],
        [InlineKeyboardButton("💬 Группа", url=GROUP_LINK)],
        [InlineKeyboardButton("🤖 Другой бот", url=OTHER_BOT_LINK)],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Вот ссылки:", reply_markup=reply_markup)

# ===== ЗАПУСК БОТА ===== #
if __name__ == "__main__":
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    # Обработчики команд
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("music", send_music))
    app.add_handler(CommandHandler("links", send_links))

    # Обработчик текстовых сообщений
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Бот запущен...")
    app.run_polling()