import logging
import os
import time

import requests
import telegram


class TgLogsHandler(logging.Handler):
    def __init__(self, bot, chat_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bot = bot
        self.chat_id = chat_id

    def emit(self, record):
        msg = self.format(record)
        self.bot.send_message(chat_id=self.chat_id, text=msg)


devman_token = os.getenv('DEVMAN_TOKEN')
tg_token = os.getenv('TG_TOKEN')
tg_chat_id = os.getenv('TG_CHAT_ID')

headers = {'Authorization': f'Token {devman_token}'}
params = {}

bot = telegram.Bot(token=tg_token)

logger = logging.getLogger("TelegramLogger")
logger.setLevel(logging.INFO)
logger.addHandler(TgLogsHandler(bot, tg_chat_id))
logger.info('Bot started.')

while True:
    try:
        response = requests.get(
            'https://dvmn.org/api/long_polling/',
            headers=headers,
            params=params,
            timeout=100
        )
        response.raise_for_status()
    except requests.exceptions.ReadTimeout:
        continue
    except requests.exceptions.ConnectionError:
        logger.error('Connection error. Retrying in 5 seconds...')
        time.sleep(5)
        continue
    except requests.HTTPError as ex:
        logger.error(str(ex))
        time.sleep(5)
        continue

    reviews = response.json()
    if reviews['status'] == 'found':
        timestamp = reviews['last_attempt_timestamp']
        for attempt in reviews['new_attempts']:
            msg = f'У вас проверена работа "{attempt["lesson_title"]}"\n'
            if attempt['is_negative']:
                msg += 'К сожалению, в работе нашлись ошибки.'
            else:
                msg += 'Работа принята!'
            bot.send_message(chat_id=tg_chat_id, text=msg)
    elif reviews['status'] == 'timeout':
        timestamp = reviews['timestamp_to_request']
    else:
        logger.error(f'Unknown answer from server: {reviews}')

    params['timestamp'] = timestamp
