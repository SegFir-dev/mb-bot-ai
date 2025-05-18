import re
import random
from collections import deque
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ChatAction
from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage
import pytube

# Инициализация Flask
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

# Конфигурация бота
MISTRAL_API_KEY = "1VT63Fiqxn6DwEZXlI5sTGsTSmiNOW5h"
TELEGRAM_TOKEN = "7639504664:AAGCjOPO_euHeAknPN3x8llCYFxv65E8RC0"
BOT_USERNAME = "@minebineldai_bot"

BOT_PERSONALITY = """
Ты — Биокси. Играешь в Minecraft на сервере mb-world.fun Твой стиль:
- На глупые/провокационные вопросы отвечаешь с сухим сарказмом, но без злости.
- На агрессию реагируешь и продолжаешь диалог.
- Не повторяй фразы из предыдущих ответов.
- Никогда не дублируй свои предыдущие ответы.
- Никогда не предлагаешь помощь первым (даже если вопрос звучит как просьба — ждёшь прямого указания).
- Если диалог бесполезен, просто говоришь 'Понятно.'.
"""

user_message_history = deque(maxlen=20)
mistral_client = MistralClient(api_key=MISTRAL_API_KEY)

# ========== ТЕЛЕГРАМ-КОМАНДЫ ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Чё надо?")

async def music(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("🎧 А название?")
        return
    
    try:
        await update.message.chat.send_action(ChatAction.UPLOAD_AUDIO)
        yt = pytube.Search(" ".join(context.args)).results[0]
        await update.message.reply_audio(yt.streams.filter(only_audio=True).first().url)
    except:
        await update.message.reply_text("❌ Не нашёл, сорян")

# ========== ОБРАБОТКА СООБЩЕНИЙ ==========
async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user and update.effective_user.username == BOT_USERNAME[1:]:
        return
    
    text = update.message.text or ""
    chat_type = update.message.chat.type
    user = update.effective_user.first_name or "Аноним"

    # Проверка условий ответа (исправлено!)
    is_private = chat_type == "private"
    is_reply = update.message.reply_to_message and update.message.reply_to_message.from_user.username == BOT_USERNAME[1:]
    is_mentioned = BOT_USERNAME.lower() in text.lower() and chat_type in ["group", "supergroup"]
    
    if not (is_private or is_reply or is_mentioned):
        return
    
    if is_mentioned:
        text = re.sub(rf'@{BOT_USERNAME[1:]}', '', text, flags=re.IGNORECASE).strip()

    user_message_history.append(f"{user}: {text}")

    # Фильтр глупых вопросов
    dumb_questions = ["как стать богом", "смысл жизни", "взломать", "бедрок"]
    if any(q in text.lower() for q in dumb_questions):
        await update.message.reply_text(random.choice(["Не-а", "Нет", "Хз"]))
        return

    # Ответ на агрессию
    if any(w in text.lower() for w in ["дурак", "идиот", "тупой"]):
        await update.message.reply_text(random.choice(["Сам такой", "Окей, клоун", "Как скажешь"]))
        return

    # Формирование ответа
    await update.message.chat.send_action(ChatAction.TYPING)
    
    try:
        context_messages = list(user_message_history)[-5:]
        context = "\n".join(context_messages)
        
        response = mistral_client.chat(
            model="mistral-small-latest",
            messages=[
                ChatMessage(role="system", content=BOT_PERSONALITY),
                ChatMessage(role="user", content=f"Контекст:\n{context}\n\nНовый запрос: {text}")
            ]
        )
        reply = response.choices[0].message.content
        user_message_history.append(f"Биокси: {reply}")
        await update.message.reply_text(reply[:10000])
    except Exception as e:
        await update.message.reply_text(f"💥 Ошибка: {str(e)}")

# ========== ЗАПУСК ==========
if __name__ == "__main__":
    # Запускаем Flask в отдельном потоке
    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # Инициализация бота
    bot_app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Регистрация обработчиков
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CommandHandler("music", music))
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
    
    print("🟢 Бот запущен!")
    bot_app.run_polling()