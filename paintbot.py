from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler, CallbackContext, MessageHandler, filters
import logging
import uuid  # Для генерации уникальных идентификаторов запросов
import asyncio
import os
from dotenv import load_dotenv
from db import get_user, add_user, users_collection
from image_generator import generate_image
from telegram import ReplyKeyboardMarkup, KeyboardButton

# Загрузка переменных окружения
load_dotenv()
TELEGRAM_API = os.getenv("TELEGRAM_API")
MONGO_LINK = os.getenv("MONGO_LINK")
MONGO_DB = os.getenv("MONGO_DB")

# Включаем логирование для отладки
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

free_generations = 10

# Функция для рассылки сообщения всем пользователям
async def broadcast_message(context: ContextTypes.DEFAULT_TYPE, message_text: str):
    # Получаем всех пользователей из базы данных
    users = users_collection.find({})
    for user in users:
        chat_id = user["chat_id"]
        try:
            await context.bot.send_message(chat_id=chat_id, text=message_text)
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения пользователю с chat_id {chat_id}: {str(e)}")


# Команда /broadcast для запуска рассылки
async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Проверка, что команда запускается только вами
    if update.effective_user.id == 380441767:  # Замените на ваш Telegram ID
        if context.args:
            message_text = " ".join(context.args)
            await broadcast_message(context, message_text)
            await update.message.reply_text("Рассылка запущена!")
        else:
            await update.message.reply_text("Пожалуйста, введите сообщение после команды /broadcast.")
    else:
        await update.message.reply_text("У вас нет прав на выполнение этой команды.")


# Функция для проверки запуска бота
async def check(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    await context.bot.send_message(chat_id=chat_id, text="Бот запущен")

# Команда /start для приветствия пользователя
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    user = get_user(chat_id)  # Проверка, зарегистрирован ли пользователь
    if not user:
        # Если пользователь новый, добавляем его в базу
        first_name = update.effective_user.first_name
        last_name = update.effective_user.last_name or ""
        username = update.effective_user.username or ""
        add_user(first_name, last_name, username, chat_id, free_generations=10)
       # Создаем Reply-клавиатуру с кнопками "Получить раскраску" и "Поддержка"
    keyboard = [
        [KeyboardButton("🎨 Получить раскраску"), KeyboardButton("💬 Поддержка")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "Привет! Я бот для генерации раскрасок. Нажмите на кнопку ниже, чтобы получить раскраску!",
        reply_markup=reply_markup
    )
  

# Обработчик для кнопки "Поддержка"
async def support_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📞 Свяжитесь с нашей поддержкой по любым вопросам:\n\n"
        "Телеграм: @support_username\n"
        "Email: support@example.com"
    )

# Обработчик нажатия кнопки "Получить раскраску"
async def handle_reply_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = get_user(chat_id)

    if user is None:
        await update.message.reply_text("Ошибка: не удалось найти пользователя в базе данных.")
        return

    # Проверяем количество бесплатных генераций
    if user["free_generations"] > 0:
        await update.message.reply_text("Пожалуйста, введите описание изображения, которое вы хотите получить:")
        context.user_data['waiting_for_description'] = True
    else:
        await update.message.reply_text(
            "Вы использовали все бесплатные генерации. Чтобы получить больше раскрасок, оформите подписку!"
        )


# Обработчик текстового ввода после нажатия на кнопку "Получить раскраску"
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = get_user(chat_id)

    if context.user_data.get('waiting_for_description') and user["free_generations"] > 0:
        context.user_data['waiting_for_description'] = False
        request_text = update.message.text
        context.args = [request_text]  # Устанавливаем аргументы для функции генерации
        
        # Генерируем уникальный идентификатор для запроса
        request_id = uuid.uuid4()
        
        # Запускаем генерацию изображения с уникальным идентификатором
        await generate_image(update, context, request_id)
        logger.info(f"[{request_id}] Генерация изображения запущена для chat_id: {chat_id}")
    else:
        await update.message.reply_text(
            "Ваши бесплатные генерации закончились. Пожалуйста, приобретите подписку для получения дополнительных раскрасок."
        )

# Обработчик нажатия кнопки "Подписаться"
async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("Чтобы подписаться, перейдите по ссылке [ссылка на оплату]")



def main():
    # Вставьте ваш токен
    application = Application.builder().token(TELEGRAM_API).build()

    # Добавляем обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler('check', check))
    application.add_handler(CommandHandler("broadcast", broadcast_command))

    # Обработчик нажатия кнопки "Получить раскраску" в Reply-клавиатуре
    application.add_handler(MessageHandler(filters.Regex("Получить раскраску"), handle_reply_button))
    # Обработчик для кнопки "Поддержка"
    application.add_handler(MessageHandler(filters.Regex("Поддержка"), support_handler))
    

    # Обработчик текстового ввода после запроса описания
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    

    
    # Запуск polling (синхронно, без await)
    application.run_polling()

if __name__ == "__main__":
    main()
