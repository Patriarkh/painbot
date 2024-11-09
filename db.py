from pymongo import MongoClient
import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

# Получаем MongoDB данные из переменных окружения
MONGO_LINK = os.getenv("MONGO_LINK")
MONGO_DB = os.getenv("MONGO_DB")
# Подключение к MongoDB
client = MongoClient(MONGO_LINK)
db = client[MONGO_DB]
users_collection = db["users"]

# Функция для добавления нового пользователя
def add_user(first_name, last_name, username, chat_id, free_generations=10):
    user = {
        "first_name": first_name,
        "last_name": last_name,
        "username": username,
        "chat_id": chat_id,
        "free_generations": free_generations
    }
    users_collection.insert_one(user)



# Функция для получения данных пользователя
def get_user(chat_id):
    return users_collection.find_one({"chat_id": chat_id})


def update_free_generations(chat_id, new_count):
    """
    Обновляет количество бесплатных генераций для пользователя.

    :param chat_id: ID чата пользователя
    :param new_count: Новое количество бесплатных генераций
    """
    users_collection.update_one(
        {"chat_id": chat_id},
        {"$set": {"free_generations": new_count}}
    )