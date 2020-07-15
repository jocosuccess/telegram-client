import configparser
import json
import csv
import string
import random
try:
    from PIL import Image
except ImportError:
    import Image
import pytesseract as tess
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
# Tessearct Environment
tess.pytesseract.tesseract_cmd = config['Telegram']['tesseract_env']
# Setting configuration values
api_id = config['Telegram']['api_id']
api_hash = config['Telegram']['api_hash']

api_hash = str(api_hash)

phone = config['Telegram']['phone']
username = config['Telegram']['username']

# Create the client and connect
client = TelegramClient(username, api_id, api_hash)

categories = ['user', 'channel', 'group']


class Ui(QtWidgets.QMainWindow):
    def __init__(self):
        super(Ui, self).__init__()
        uic.loadUi(GUI_DIR + '/' + gui_file, self)
        # parameter
        self.chat_list = []
        self.cat_number = None
        self.chat_id = {}
        self.entity_id = None
        self.chat_selected = False

        # GUI
        self.extract_btn = self.findChild(QtWidgets.QPushButton, 'extract_btn')
        self.start_time_widget = self.findChild(QtWidgets.QDateTimeEdit, 'start_time_widget')
        self.start_time_widget.setDateTime(datetime.now())
        self.end_time_widget = self.findChild(QtWidgets.QDateTimeEdit, 'end_time_widget')
        self.end_time_widget.setDateTime(datetime.now())
        self.chat_tbl_widget = self.findChild(QtWidgets.QTableWidget, 'chat_tbl')
        self.chat_tbl_widget.cellClicked.connect(self.table_chat_click)
        self.extract_btn.clicked.connect(self.extractButtonClick)

        with client:
            client.loop.run_until_complete(self.get_chat_list(phone))
        self.add_chat_table(self.chat_list)

        self.show()

    def table_chat_click(self, row, column):
        if column == 1:
            self.chat_selected = True
            category = self.chat_tbl_widget.item(row, 0).text()
            chat_name = self.chat_tbl_widget.item(row, 1).text()
            if category == 'user':
                self.cat_number = 0
            elif category == 'channel':
                self.cat_number = 1
            elif category == 'group':
                self.cat_number = 2
            else:
                pass
            self.entity_id = self.chat_id[chat_name]
        else:
            self.chat_selected = False

    def add_chat_table(self, chat_list):
        for chat in chat_list:
            rowPosition = self.chat_tbl_widget.rowCount()
            self.chat_tbl_widget.insertRow(rowPosition)
            # numcols = self.chat_tbl_widget.columnCount()
            numrows = self.chat_tbl_widget.rowCount()
            self.chat_tbl_widget.setRowCount(numrows)
            # self.chat_tbl_widget.setColumnCount(4)
            self.chat_tbl_widget.setItem(numrows - 1, 0, QtWidgets.QTableWidgetItem(chat['category']))
            self.chat_tbl_widget.setItem(numrows - 1, 1, QtWidgets.QTableWidgetItem(chat['chat_name']))

    def extractButtonClick(self):
        start_time = self.start_time_widget.dateTime()
        end_time = self.end_time_widget.dateTime()
        if not self.chat_selected:
            self.show_message_box("Warning", "Select a chat")
            return
        else:
            with client:
                client.loop.run_until_complete(self.get_messages(self.entity_id, self.cat_number, start_time, end_time))

    def show_message_box(self, title, message):
        msg = QtWidgets.QMessageBox()
        msg.setWindowTitle(title)
        msg.setText(message)
        retval = msg.exec_()

    async def get_chat_list(self, phone):
        await client.start()
        print("Client Created")
        # Ensure you're authorized
        if await client.is_user_authorized() == False:
            self.show_message_box("Error", "Auth Failed...")
            return
            # await client.send_code_request(phone)
            # try:
            #     await client.sign_in(phone, input('Enter the code: '))
            # except SessionPasswordNeededError:
            #     await client.sign_in(password=input('Password: '))

        me = await client.get_me()

        for chat in await client.get_dialogs():
            print('name:{0} id:{1} is_user:{2} is_channel:{3} is_group:{4}'.format(chat.name, chat.id, chat.is_user, chat.is_channel, chat.is_group))
            if chat.is_user:
                chat_id = str(chat.id)
                cat_number = 0
                continue
            if chat.is_channel:
                chat_id = str(chat.id)[4:]
                cat_number = 1
            if not chat.is_channel and chat.is_group:
                chat_id = str(chat.id)[1:]
                cat_number = 2
            self.chat_id[chat.name] = chat.id
            each_chat = dict(category=categories[cat_number], chat_name=chat.name, chat_id=chat_id)
            print(each_chat)
            self.chat_list.append(each_chat)

    async def get_messages(self, entity_id, number, start_time, end_time):
        entity = await client.get_entity(entity_id)
        if number == 0:
            chat_id = str(entity_id)
        if number == 1:
            chat_id = str(entity_id)[4:]
        if number == 2:
            chat_id = str(entity_id)[1:]
        offset_id = 0
        limit = 100
        all_messages = []
        total_messages = 0
        total_count_limit = 0
        sn = 0
        code = ''.join(random.sample((string.ascii_uppercase+string.digits), 6))
        file_path = CSV_DIR + '/' + code + '.csv'
        with open(file_path, 'w', newline='', encoding="utf-8") as csv_file:
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
                    print(message)
                    text = ''
                    if start_time <= message.date <= end_time:
                        if message.message is not None and not message.message == '':
                            text = message.message
                        elif message.media is not None:
                            download_path = await client.download_media(
                                message.media, MEDIA_DIR
                            )
                            try:
                                text = tess.image_to_string(Image.open(download_path))
                            except Exception as e :
                                self.show_message_box("Error", "No Tesseract")
                            # if 'photo' in message.media:
                            #     photo = message.media.photo
                            #     photo_1 = Image.open(photo)
                            #     image_buf = BytesIO()
                            #     photo_1.save(image_buf, format="JPEG")
                            #     image = image_buf.getvalue()
                            # elif 'document' in message.media.key():
                            #     photo = message.media.document
                                # photo_1 = Image.open(photo)
                                # image_buf = BytesIO()
                                # photo_1.save(image_buf, format="JPEG")
                                # image = image_buf.getvalue()
                        else:
                            continue
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
                        row = [sn, direction, text, message.date.strftime("%Y-%m-%d %H:%M:%S")]
                        writer.writerow(row)

                            # all_messages.append(message.to_dict())
                offset_id = messages[len(messages) - 1].id
                # total_messages = len(all_messages)
                # if total_count_limit != 0 and total_messages >= total_count_limit:
                #     break
        self.show_message_box("Success", code)
        return


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = Ui()
    app.exec_()
