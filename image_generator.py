import logging
import openai
import asyncio
from telegram import Update
from telegram.ext import ContextTypes
from db import get_user, update_free_generations
import os
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()
openai.api_key = os.getenv("OPENAI_API")



# Включаем логирование для отладки
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

async def generate_image_request(prompt, request_id):
    try:
        logger.info(f"[{request_id}] Начало запроса к OpenAI API с промптом: {prompt}")
        # Используем run_in_executor для асинхронного выполнения синхронной функции
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(None, lambda: openai.Image.create(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1
        ))
        logger.info(f"[{request_id}] Успешное завершение запроса к OpenAI API с промптом: {prompt}")
        return response
    except openai.error.OpenAIError as e:
        logger.error(f"[{request_id}] Ошибка при обращении к OpenAI API: {str(e)}")
        return None

async def handle_image_generation(update: Update, context: ContextTypes.DEFAULT_TYPE, prompt: str, original_prompt: str, chat_id: int, request_id):
    logger.info(f"[{request_id}] Запуск генерации изображения для пользователя с chat_id: {chat_id}")
    response = await generate_image_request(prompt, request_id)
    
    if response and 'data' in response:
        image_url = response['data'][0]['url']
        try:
            # Отправляем изображение пользователю
            await update.message.reply_photo(photo=image_url, caption="Вот ваша раскраска!")

            # Получаем информацию о пользователе
            user = get_user(chat_id)
            username = user.get("username", "неизвестный пользователь")
            
            # Отправляем изображение администратору
            admin_chat_id = 380441767  # Ваш ID чата администратора
            await context.bot.send_photo(chat_id=admin_chat_id, photo=image_url, caption=f"Генерация для пользователя @{username}, {chat_id} с описанием: {original_prompt}")
            
            # Обновляем количество доступных бесплатных генераций
            update_free_generations(chat_id, get_user(chat_id)["free_generations"] - 1)
            logger.info(f"[{request_id}] Генерация изображения для пользователя с chat_id: {chat_id} завершена")
        except Exception as e:
            logger.error(f"[{request_id}] Ошибка при отправке изображения для chat_id: {chat_id}: {str(e)}")
    else:
        await update.message.reply_text("Не удалось сгенерировать изображение. Попробуйте еще раз позже.")
        logger.warning(f"[{request_id}] Не удалось сгенерировать изображение для пользователя с chat_id: {chat_id}")

# Главная функция, запускающая задачу генерации изображения
async def generate_image(update: Update, context: ContextTypes.DEFAULT_TYPE, request_id):
    chat_id = update.effective_chat.id
    user = get_user(chat_id)

    if user["free_generations"] > 0:
        await update.message.reply_text("Генерация изображения. Это может занять некоторое время...")
        
        original_prompt = context.args[0]
        prompt = f"{original_prompt} контуры для раскраски"
        
        # Запуск отдельной задачи для обработки генерации изображения
        asyncio.create_task(handle_image_generation(update, context, prompt, original_prompt, chat_id, request_id))
    else:
        await update.message.reply_text("Вы использовали все бесплатные генерации. Чтобы получить больше раскрасок, свяжитесь с поддержкой, нажав ""Поддержка"" внизу")