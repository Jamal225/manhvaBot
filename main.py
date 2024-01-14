import asyncio
import logging
from collections import deque
from telethon import TelegramClient

from telegram_parser import telegram_parser
from utils import create_logger, get_history, send_error_message
from config import *

api_id, api_hash, manhva_chat_id, bot_token = API_ID, API_HASH, \
                                              MANHVA_CHANNEL_ID, BOT_TOKEN
###########################
# Можно добавить телеграм канал

telegram_channels = {
    1001551236459: 'https: // t.me / lrmanga',
}


def check_pattern_func(text):
    words = text.lower().split()

    key_words = [
        'глава'
    ]

    for word in words:
        if 'глава' in word and len(word) < 6:
            return True

        for key in key_words:
            if key in word:
                return True

    return False


###########################

# 50 первых символов от поста - это ключ для поиска повторных постов
n_test_chars = 50

# Количество уже опубликованных постов, чтобы их не повторять
amount_messages = 50

# Очередь уже опубликованных постов
posted_q = deque(maxlen=amount_messages)

# +/- интервал между запросами у  кастомного парсеров в секундах
timeout = 2

###########################


logger = create_logger('manhva')
logger.info('Start...')

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

tele_logger = create_logger('telethon', level=logging.ERROR)

bot = TelegramClient('bot', api_id, api_hash,
                     base_logger=tele_logger, loop=loop)
bot.start(bot_token=bot_token)


async def send_message_func(text):
    '''Отправляет посты в канал через бот'''
    await bot.send_message(entity=manhva_chat_id,
                           parse_mode='html', link_preview=False, message=text)

    logger.info(text)

# Телеграм парсер
client = telegram_parser('manhva', api_id, api_hash, telegram_channels, posted_q,
                         n_test_chars, check_pattern_func, send_message_func,
                         tele_logger, loop)

# Список из уже опубликованных постов, чтобы их не дублировать
history = loop.run_until_complete(get_history(client, manhva_chat_id,
                                              n_test_chars, amount_messages))

posted_q.extend(history)

try:
    # Запускает все парсеры
    client.run_until_disconnected()

except Exception as e:
    message = f'&#9888; ERROR: telegram parser (all parsers) is down! \n{e}'
    loop.run_until_complete(send_error_message(message, bot_token,
                                               manhva_chat_id, logger))
finally:
    loop.close()
