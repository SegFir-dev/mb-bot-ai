import os
import re
from telegram import Update
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

# --- КОНФИГУРАЦИЯ ---
MISTRAL_API_KEY = "1VT63Fiqxn6DwEZXlI5sTGsTSmiNOW5h"  # Замените на свой ключ
TELEGRAM_TOKEN = "7639504664:AAGCjOPO_euHeAknPN3x8llCYFxv65E8RC0"         # Получить у @BotFather
BOT_USERNAME = "@minebineldai_bot"       # Например: "@my_ai_bot" (с @)

# Настройки личности бота
BOT_PERSONALITY = """
Ты дружелюбный ИИ-помощник. Отвечай кратко и вежливо. 
Не пиши длинные сообщения. Будь полезным и общительным.
"""

# Ссылки для команды /links
CHANNEL_LINK = "https://t.me/minebineld"
GROUP_LINK = "https://t.me/minebineldchat"
BOT_LINK = "https://t.me/minebineldbot"

# Инициализация Mistral
mistral_client = MistralClient(api_key=MISTRAL_API_KEY)

# --- КОМАНДЫ БОТА ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    await update.message.reply_text("🤖 Привет! Я твой ИИ-помощник. Напиши мне что-нибудь!")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    help_text = """
📌 Доступные команды:
/start - Начать общение
/help - Помощь
/music [название] - Найти музыку
/links - Полезные ссылки
"""
    await update.message.reply_text(help_text)

async def send_music(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Поиск и отправка музыки"""
    query = " ".join(context.args)
    if not query:
        await update.message.reply_text("❌ Укажите название трека: /music Coldplay - Yellow")
        return

    try:
        await update.message.chat.send_action(action="typing")
        yt = pytube.Search(query).results[0]
        audio_url = yt.streams.filter(only_audio=True).first().url
        await update.message.reply_audio(audio_url, title=yt.title)
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}")

async def send_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправка полезных ссылок"""
    links_text = f"""
🔗 Полезные ссылки:
Канал: {CHANNEL_LINK}
Группа: {GROUP_LINK}
Бот: {BOT_LINK}
"""
    await update.message.reply_text(links_text)

# --- ОБРАБОТКА СООБЩЕНИЙ ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка всех текстовых сообщений"""
    message_type = update.message.chat.type
    text = update.message.text or ""

    # Для групп/супергрупп проверяем упоминание
    if message_type in ["group", "supergroup"]:
        if BOT_USERNAME.lower() not in text.lower():
            return  # Игнорируем без упоминания
        
        # Удаляем упоминание из текста (регистронезависимо)
        text = re.sub(rf'@{BOT_USERNAME[1:]}', '', text, flags=re.IGNORECASE).strip()
        if not text:
            return  # Игнорируем пустые сообщения после удаления упоминания

    # Для ЛС обрабатываем все сообщения
    await update.message.chat.send_action(action="typing")
    
    try:
        # Запрос к Mistral API
        response = mistral_client.chat(
            model="mistral-small-latest",
            messages=[ChatMessage(role="user", content=BOT_PERSONALITY + "\n\n" + text)],
        )
        await update.message.reply_text(response.choices[0].message.content)
    except Exception as e:
        await update.message.reply_text(f"⚠️ Ошибка: {str(e)}")

# --- ЗАПУСК БОТА ---
if __name__ == "__main__":
    print("🚀 Бот запускается...")
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    # Команды
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("music", send_music))
    app.add_handler(CommandHandler("links", send_links))

    # Обработка текстовых сообщений
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Запуск
    print("🤖 Бот готов к работе!")
    app.run_polling()