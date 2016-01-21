#!/usr/bin/env python3

import time
import requests
import re
import random
import tempfile
import subprocess
import json
from simplejson.scanner import JSONDecodeError


with open('settings.json') as f:
    settings  = json.load(f) # smells
    TOKEN = settings['token']


class SimpleBot:
    URL = "https://api.telegram.org/bot%s/%s"
    HELP_MESSAGE = """
    Добро пожаловать в гости к боту, доступные команды:
    /rand - получить случайное число
    /echo [ваше сообщение] - ответить тем же сообщением
    /say [ваше сообщение] - ответить тем же сообщением голосом
    """
    def __init__(self, token):
        self.token = token
        self.last_update_id = 0

    def api_call(self, method, file_data=None, **params):
        kwargs = {}
        if file_data:
            print(file_data)
            kwargs['files'] = {
                'audio': file_data
            }
        resp = requests.post(self.URL % (self.token, method), params=params, **kwargs)
        try:
            data = resp.json()
        except JSONDecodeError:
            return None
        print(data)
        if 'result' in data:
            return data['result']
        return None # Todo raise
    def run(self):
        while True:
            updates = self.api_call('getUpdates', offset=self.last_update_id + 1, timeout=10)
            if updates:
                for update in updates:
                    self.process_update(update)
            time.sleep(1)

    def process_update(self, update):
        print(update)
        if 'message' in update and 'text' in update['message']:
            chat_id = update['message']['chat']['id']
            text = update['message']['text']
            if text == '/help':
                self.send_message(chat_id, self.HELP_MESSAGE)
            elif text.startswith('/echo'):
                msg = re.match(r'/echo\s*(.+)', text)
                if msg:
                    self.send_message(chat_id, msg.group(1))
                else:
                    self.send_message(chat_id, self.HELP_MESSAGE)
            elif text.startswith('/say'):
                msg = re.match(r'/say\s*(.+)', text)
                if msg:
                    with tempfile.NamedTemporaryFile() as f:
                        subprocess.call(['say', '-o', f.name, msg.group(1)])
                        subprocess.call(['ffmpeg', '-i', f.name + '.aiff', '-acodec', 'libopus', f.name + '.ogg', '-y'])
                        ff = open(f.name + '.ogg', 'rb')
                        self.send_audio(chat_id, ff)
                        # todo remove
                else:
                    self.send_message(chat_id, self.HELP_MESSAGE)
            elif text.startswith('/rand'):
                self.send_message(chat_id, '%d' % random.randrange(0, 10))
            else:
                self.send_message(chat_id, self.HELP_MESSAGE)
        self.last_update_id = int(update['update_id'])
    def send_audio(self, chat_id, file_data):
        self.api_call('sendAudio', chat_id=chat_id, file_data=file_data)

    def send_message(self, chat_id, text):
        self.api_call('sendMessage', chat_id=chat_id, text=text)


bot = SimpleBot(TOKEN)
print("Bot starting...")
bot.run()
