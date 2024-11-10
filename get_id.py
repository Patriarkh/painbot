import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "7207824724:AAE7zfp9-dNFctMPeGZPwHul7KXcM14EqGA"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Привет! Отправь мне файл или фото, и я верну его ID.")

# Обработка файлов и фотографий
async def file_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Проверка на документ (файл)
    if update.message.document:
        file_id = update.message.document.file_id  # Получение ID документа
        await update.message.reply_text(f"ID вашего файла: {file_id}")
    
    # Проверка на фото
    elif update.message.photo:
        file_id = update.message.photo[-1].file_id  # Получение ID последней (наибольшей) версии фото
        await update.message.reply_text(f"ID вашего фото: {file_id}")
    else:
        await update.message.reply_text("Отправьте файл или фото, чтобы получить его ID.")

if __name__ == "__main__":
    application = ApplicationBuilder().token(TOKEN).build()
    
    # Команда /start
    application.add_handler(CommandHandler("start", start))
    
    # Обработчик для получения ID файлов и фотографий
    application.add_handler(MessageHandler(filters.Document.ALL | filters.PHOTO, file_handler))
    
    # Запуск бота
    application.run_polling()