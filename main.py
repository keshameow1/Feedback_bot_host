import asyncio
from aiogram import Bot, Dispatcher, types
import logging
import os
from dotenv import load_dotenv

# Загрузить переменные из файла .env
load_dotenv()


# Установка уровня логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота
bot = Bot(token=os.getenv("TOKEN"))
dp = Dispatcher(bot)

ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID")) # ID вашей группы в Telegram

# словарь для хранения времени последнего сообщения от каждого пользователя
last_message_time = {}

# константы для ограничения флуда
FLOOD_LIMIT = 30  # время в секундах между сообщениями
FLOOD_MESSAGE = "Слишком быстро! Попробуйте еще раз через {time_left} секунд"


# Обработка команды /start
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    #Отправляем приветствие
    await message.answer("Привет! Я бот обратной связи. Напишите свой вопрос или отзыв, и я перешлю его администратору.")


# Обработка команды /ответ
@dp.message_handler(commands=['ответ'])
async def send_reply(message: types.Message):
    #Проверяем что команда отправлена из админского чата
    if message.chat.id != int(ADMIN_CHAT_ID):
        return

    try:
        # Получаем идентификатор пользователя и текст ответа из сообщения
        user_id, reply_text = message.text.split(maxsplit=2)[1:]
        # Преобразуем идентификатор пользователя в целочисленный тип
        user_id = int(user_id)

        # Отправляем ответ пользователю
        await bot.send_message(chat_id=user_id, text=reply_text)

        # Отправляем подтверждение об успешной отправке ответа администратору
        await message.answer('Ответ успешно отправлен!')
    except ValueError:
        # Если в сообщении отсутствует идентификатор пользователя или текст ответа, отправляем сообщение об ошибке
        await message.answer('Пожалуйста, введите команду в формате /ответ {user_id} {текст ответа}')
    except Exception as e:
        print(f'Произошла ошибка: {e}')


# хендлер на текстовые сообщения
@dp.message_handler(content_types=["text"])
async def handle_text(message: types.Message):
    if (message.chat.type != 'private'):
        return
    user_id = message.from_user.id
    current_time = asyncio.get_running_loop().time()
    # Если пользователь отправил сообщение менее 30 секунд назад, блокируем его сообщение и выводим обратный отсчет
    if user_id in last_message_time and current_time - last_message_time[user_id] < 10:
        remaining_time = int(10 - (current_time - last_message_time[user_id]))
        msg = await message.answer(
            f"Вы отправили сообщение слишком часто. Попробуйте еще раз через {remaining_time} секунд")
        # Запускаем цикл для автообновления сообщения
        for i in range(remaining_time, 0, -1):
            await asyncio.sleep(1)
            remaining_time -= 1
            if remaining_time == 0:
                # Обновляем сообщение с новым текстом
                await bot.edit_message_text("Вы снова можете писать", chat_id=msg.chat.id, message_id=msg.message_id)
            else:
                # Обновляем сообщение с новым обратным отсчетом
                await bot.edit_message_text(
                    f"Вы отправили сообщение слишком часто. Попробуйте еще раз через {remaining_time} секунд",
                    chat_id=msg.chat.id, message_id=msg.message_id)
        return
    # Если пользователь отправил сообщение более 30 секунд назад, сохраняем время его последнего сообщения
    last_message_time[user_id] = current_time

    # Отправка сообщения администратору
    await bot.send_message(ADMIN_CHAT_ID, f'Новое сообщение от {message.chat.first_name} \nID: {message.chat.id}\n'
                                     f'Текст сообщения:\n\n_{message.text}_\n\n`/ответ {message.chat.id} `',
                           parse_mode='Markdown')

    # Отправка сообщения пользователю
    await message.answer("Спасибо за ваше сообщение! Мы рассмотрим его в ближайшее время.")




# Запуск бота
if __name__ == '__main__':
    asyncio.run(dp.start_polling())
