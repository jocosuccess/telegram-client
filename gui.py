import configparser
import json
import csv
import string
import random
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
import asyncio
from datetime import date, datetime

from PyQt5 import QtWidgets, uic
import sys
from utils.constants import *

from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.tl.functions.messages import (GetHistoryRequest)
from telethon.tl.functions.messages import (GetDialogsRequest)
from telethon.tl.types import (PeerChannel, PeerChat, PeerUser)
from telethon.tl.types import (InputPeerEmpty)

from utils.constants import *

# Reading Configs
config = configparser.ConfigParser()
config.read(CRED_DIR + '/' + credential_file)

# Setting configuration values
api_id = config['Telegram']['api_id']
api_hash = config['Telegram']['api_hash']

api_hash = str(api_hash)

phone = config['Telegram']['phone']
username = config['Telegram']['username']

# Create the client and connect
client = TelegramClient(username, api_id, api_hash)


class Ui(QtWidgets.QMainWindow):
    def __init__(self):
        super(Ui, self).__init__()
        uic.loadUi(GUI_DIR + '/' + gui_file, self)
        self.extract_btn = self.findChild(QtWidgets.QPushButton, 'extract_btn')
        self.start_time = self.findChild(QtWidgets.QDateTimeEdit, 'start_time')
        self.end_time = self.findChild(QtWidgets.QDateTimeEdit, 'end_time')
        self.chat_list = self.findChild(QtWidgets.QListWidget, 'chat_list')
        self.extract_btn.clicked.connect(self.extractButtonClick)

        with client:
            client.loop.run_until_complete(main(phone))

        self.show()

    def extractButtonClick(self):
        print('ExtractButton Clicked')


async def get_messages(entity, chat_id, number):
    offset_id = 0
    limit = 100
    all_messages = []
    total_messages = 0
    total_count_limit = 0
    sn = 0
    filename = ''.join(random.sample((string.ascii_uppercase + string.digits), 6)) + '.csv'
    with open(filename, 'w', newline='', encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["SN", "Direction", "Message", "Date"])
        while True:
            # print("Current Offset ID is:", offset_id, "; Total Messages:", total_messages)
            history = await client(GetHistoryRequest(
                peer=entity,
                offset_id=offset_id,
                offset_date=None,
                add_offset=0,
                limit=limit,
                max_id=0,
                min_id=0,
                hash=0
            ))
            if not history.messages:
                break
            messages = history.messages
            for message in messages:
                if message.message is not None:
                    sn = sn + 1
                    id = None
                    direction = 'Reply'
                    if number == 0:
                        id = message.to_id.user_id
                    elif number == 1:
                        id = message.to_id.channel_id
                    elif number == 2:
                        id = message.to_id.chat_id
                    else:
                        pass
                    if int(chat_id) == id:
                        direction = 'Origin'
                    row = [sn, direction, message.message, message.date.strftime("%Y-%m-%d %H:%M:%S")]
                    writer.writerow(row)

                    all_messages.append(message.to_dict())
            offset_id = messages[len(messages) - 1].id
            total_messages = len(all_messages)
            if total_count_limit != 0 and total_messages >= total_count_limit:
                break
    return all_messages
    # with open('channel_messages.json', 'w') as outfile:
    #     json.dump(all_messages, outfile, cls=DateTimeEncoder)


async def main(phone):
    await client.start()
    print("Client Created")
    # Ensure you're authorized
    if await client.is_user_authorized() == False:
        await client.send_code_request(phone)
        try:
            await client.sign_in(phone, input('Enter the code: '))
        except SessionPasswordNeededError:
            await client.sign_in(password=input('Password: '))

    me = await client.get_me()

    for chat in await client.get_dialogs():
        # print('name:{0} id:{1} is_user:{2} is_channel:{3} is_group:{4}'.format(chat.name, chat.id, chat.is_user, chat.is_channel, chat.is_group))
        number = None
        if chat.is_user:
            chat_id = str(chat.id)
            number = 0
        if chat.is_channel:
            chat_id = str(chat.id)[4:]
            number = 1
        if not chat.is_channel and chat.is_group:
            chat_id = str(chat.id)[1:]
            number = 2
        entity = await client.get_entity(chat.id)
        print('*******************' + chat.name + '*************************')
        all_messages = await get_messages(entity, chat_id, number)
        # print(all_messages)


if __name__ == '__main__':
    with client:
        client.loop.run_until_complete(main(phone))
