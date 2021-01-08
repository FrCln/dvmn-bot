import logging
import os
import time

import requests
import telegram


logging.basicConfig(filename="bot.log", level=logging.INFO)

devman_token = os.getenv('DEVMAN_TOKEN')
tg_token = os.getenv('TG_TOKEN')
tg_chat_id = os.getenv('TG_CHAT_ID')

headers = {'Authorization': f'Token {devman_token}'}
params = {}

bot = telegram.Bot(token=tg_token)
logging.info('Bot started.')

while True:
    try:
        response = requests.get('https://dvmn.org/api/long_polling/', headers=headers, params=params, timeout=100)
        response.raise_for_status()
    except requests.exceptions.ReadTimeout:
        continue
    except requests.exceptions.ConnectionError:
        logging.error('Connection error. Retrying in 5 seconds...')
        time.sleep(5)
        continue
    except requests.HTTPError as ex:
        logging.error(str(ex))
        time.sleep(5)
        continue

    reviews = response.json()
    if reviews['status'] == 'found':
        logging.info('New checked task found.')
        timestamp = reviews['last_attempt_timestamp']
        for attempt in reviews['new_attempts']:
            msg = f'У вас проверена работа "{attempt["lesson_title"]}"\n'
            if attempt['is_negative']:
                msg += 'К сожалению, в работе нашлись ошибки.'
            else:
                msg += 'Работа принята!'
            bot.send_message(chat_id=tg_chat_id, text=msg)
            logging.info('Message sent.')
    elif reviews['status'] == 'timeout':
        timestamp = reviews['timestamp_to_request']
    else:
        logging.error(f'Unknown answer from server: {reviews}')

    params['timestamp'] = timestamp
