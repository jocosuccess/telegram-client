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
from telethon.errors import SessionPasswordNeededError, PhoneNumberUnoccupiedError
import asyncio
from datetime import date, datetime

from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QTableWidget, QDateTimeEdit, QTableWidgetItem, QVBoxLayout, QMessageBox, QWidget, QStackedWidget, QLineEdit, QInputDialog
from PyQt5 import uic
import sys
from utils.constants import *

from telethon.sync import TelegramClient
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
api_id = 695236
api_hash = '358d0a4e0cfff381f9cec02e438ef7f0'

api_hash = str(api_hash)


# Create the client and connect
client = TelegramClient("telegram", api_id, api_hash)

categories = ['user', 'channel', 'group']
window = None


class MainUI(QMainWindow):
    def __init__(self):
        super(MainUI, self).__init__()
        uic.loadUi(GUI_DIR + '/' + main_ui_file, self)
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        # self.check_sign()

    # async def check_sign(self):
    #     client.connect()
    #     if client.is_user_authorized():
    #     telegram_widget = TelegramWidget(self)
    #     self.stacked_widget.addWidget(telegram_widget)
        # else:
        login_widget = LoginWidget(self)
        self.stacked_widget.addWidget(login_widget)
        # self.stacked_widget.setCurrentWidget(login_widget)
        # self.show()

    def show_telegram(self):
        telegram_widget = TelegramWidget(self)
        self.stacked_widget.addWidget(telegram_widget)
        self.stacked_widget.setCurrentWidget(telegram_widget)


class LoginWidget(QWidget):
    def __init__(self, parent=None):
        super(LoginWidget, self).__init__(parent)
        uic.loadUi(GUI_DIR + '/' + login_ui_file, self)
        self.phone_txt = self.findChild(QLineEdit, 'phone_txt')
        self.connection_btn = self.findChild(QPushButton, 'connection_btn')
        self.connection_btn.clicked.connect(self.telegram_connect)

    def telegram_connect(self):
        phone_number = self.phone_txt.text()
        if phone_number is None or phone_number == '':
            self.show_message_box("Warning", "Insert PhoneNumber")
            return
        client.connect()
        if not client.is_user_authorized():
            try:
                client.send_code_request(phone_number)
            except TypeError:
                self.show_message_box("Warning", "Invalid Number")
            code, ok = QInputDialog.getText(self, "Authorize", "", QLineEdit.Normal)
            if ok:
                try:
                    me = client.sign_in(phone_number, code)
                except SessionPasswordNeededError:
                    self.show_message_box("Warning", "Need Password")
                    return
                except PhoneNumberUnoccupiedError:
                    self.show_message_box("Warning", "Sign Up")
                    return
        window.show_telegram()

    def show_message_box(self, title, message):
        msg = QMessageBox()
        msg.setWindowTitle(title)
        msg.setText(message)
        retval = msg.exec_()


class TelegramWidget(QWidget):
    def __init__(self, parent=None):
        super(TelegramWidget, self).__init__(parent)
        uic.loadUi(GUI_DIR + '/' + telegram_ui_file, self)
        self.chat_list = []
        self.cat_number = None
        self.chat_id = {}
        self.category_id = {}
        self.entity_id = None
        self.chat_selected = False

        self.extract_btn = self.findChild(QPushButton, 'extract_btn')
        self.start_time_widget = self.findChild(QDateTimeEdit, 'start_time_widget')
        self.start_time_widget.setDateTime(datetime.now())
        self.end_time_widget = self.findChild(QDateTimeEdit, 'end_time_widget')
        self.end_time_widget.setDateTime(datetime.now())
        self.chat_tbl_widget = self.findChild(QTableWidget, 'chat_tbl')
        self.chat_tbl_widget.cellClicked.connect(self.table_chat_click)
        self.extract_btn.clicked.connect(self.extractButtonClick)
        with client:
            client.loop.run_until_complete(self.get_chat_list())
        self.add_chat_table(self.chat_list)
        # self.show()

    def table_chat_click(self, row, column):
        if column == 0:
            self.chat_selected = True
            chat_name = self.chat_tbl_widget.item(row, 0).text()
            self.cat_number = self.category_id[chat_name]
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
            self.chat_tbl_widget.setItem(numrows - 1, 0, QTableWidgetItem(chat['chat_name']))

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
        msg = QMessageBox()
        msg.setWindowTitle(title)
        msg.setText(message)
        retval = msg.exec_()

    async def get_chat_list(self):
        # await client.start()
        print("Client Created")
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
            self.category_id[chat.name] = cat_number
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
                            except Exception as e:
                                self.show_message_box("Error", "No Tesseract")
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
                offset_id = messages[len(messages) - 1].id
        self.show_message_box("Success", code)
        return


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainUI()
    window.show()
    app.exec_()
