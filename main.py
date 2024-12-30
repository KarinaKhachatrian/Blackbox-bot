import logging
from aiogram import Bot, Dispatcher, types
import g4f
from aiogram.utils import executor
from dotenv import load_dotenv
import os

logging.basicConfig(level=logging.INFO)
load_dotenv()
TOKEN = os.getenv("TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

conversation_history = {}

def trim_history(history, max_length=4096):
    current_length = sum(len(message["content"]) for message in history)
    while history and current_length > max_length:
        removed_message = history.pop(0)
        current_length -= len(removed_message["content"])
    return history

@dp.message_handler(commands=['clear'])
async def process_clear_command(message: types.Message):
    user_id = message.from_user.id
    conversation_history[user_id] = []
    await message.reply("История диалога очищена.")

@dp.message_handler()
async def send_welcome(message: types.Message):
    user_id = message.from_user.id
    user_input = message.text

    if user_id not in conversation_history:
        conversation_history[user_id] = []

    conversation_history[user_id].append({"role": "user", "content": user_input})
    conversation_history[user_id] = trim_history(conversation_history[user_id])

    chat_history = conversation_history[user_id]

    generating_message = await message.answer("Подождите...")
    try:
        response = await g4f.ChatCompletion.create_async(
            model=g4f.models.default,
            messages=chat_history,
            provider=g4f.Provider.Blackbox,
        )
        chat_gpt_response = response

    except Exception as e:
        print(f"{g4f.Provider.Blackbox.__name__}:", e)
        chat_gpt_response = "Извините, произошла ошибка."

    await bot.delete_message(chat_id=message.chat.id, message_id=generating_message.message_id)

    conversation_history[user_id].append({"role": "assistant", "content": chat_gpt_response})
    print(conversation_history)
    length = sum(len(message["content"]) for message in conversation_history[user_id])
    print(length)

    await message.answer(chat_gpt_response)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
