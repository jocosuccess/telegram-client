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
from telethon.errors import SessionPasswordNeededError, PhoneNumberUnoccupiedError, FloodWaitError
import asyncio
from datetime import date, datetime

from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QTableWidget, QDateTimeEdit, QTableWidgetItem, QVBoxLayout, QMessageBox, QWidget, QStackedWidget, QLineEdit, QInputDialog, QListWidget, QLabel
from PyQt5 import uic, QtGui, QtCore
import sys
from utils.constants import *

from telethon.sync import TelegramClient
from telethon.tl.functions.messages import (GetHistoryRequest)
from telethon.tl.functions.messages import (GetDialogsRequest)
from telethon.tl.types import (PeerChannel, PeerChat, PeerUser)
from telethon.tl.types import (InputPeerEmpty)

from utils.constants import *

# Tessearct Environment
tess.pytesseract.tesseract_cmd = tesseract_env
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
        self.setFixedSize(530, 630)
        self.setWindowIcon(QtGui.QIcon(GUI_DIR + '/TelegramFxBacktest.png'))
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        login_widget = LoginWidget(self)
        self.stacked_widget.addWidget(login_widget)

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
        self.status_login_lbl = self.findChild(QLabel, 'status_login_lbl')
        self.status_login_lbl.setText('Status:  Not Connected')

    def telegram_connect(self):
        phone_number = self.phone_txt.text()
        if phone_number is None or phone_number == '':
            self.show_message_box("Warning", "Insert PhoneNumber")
            return
        client.connect()
        if client.is_user_authorized() and '+' + client.get_me().phone == phone_number:
            # if '+' + client.get_me().phone == phone_number:
            pass
        else:
            try:
                client.send_code_request(phone_number)
            except TypeError:
                self.show_message_box("Warning", "Invalid Number")
                return
            except FloodWaitError:
                self.show_message_box("Warning", "too much request")
                return
            code, ok = QInputDialog.getText(self, "Authorize", "", QLineEdit.Normal)
            if ok:
                if code is None or code == '':
                    return
                try:
                    me = client.sign_in(phone_number, code)
                except SessionPasswordNeededError:
                    self.show_message_box("Warning", "Need Password")
                    return
                except PhoneNumberUnoccupiedError:
                    self.show_message_box("Warning", "Sign Up")
                    return
            else:
                return
        me = client.get_me().phone
        print(me)
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
        self.chat_list_widget = self.findChild(QListWidget, 'chat_list_widget')
        self.chat_list_widget.clicked.connect(self.list_view_clicked)
        self.extract_btn.clicked.connect(self.extractButtonClick)
        self.status_telegram_lbl = self.findChild(QLabel, 'status_telegram_lbl')
        self.status_telegram_lbl.setText('Status:   Connected')
        with client:
            client.loop.run_until_complete(self.get_chat_list())
        self.add_chat_list(self.chat_list)

    def list_view_clicked(self):
        item = self.chat_list_widget.currentItem()
        self.chat_selected = True
        chat_name = str(item.text())
        self.entity_id = self.chat_id[chat_name]

    def add_chat_list(self, chat_list):
        i = 0
        for chat in chat_list:
            self.chat_list_widget.insertItem(i, chat['chat_name'])
            i = i + 1

    def extractButtonClick(self):
        start_time = self.start_time_widget.dateTime()
        end_time = self.end_time_widget.dateTime()
        if not self.chat_selected:
            self.show_message_box("Warning", "Select a chat")
            return
        else:
            with client:
                client.loop.run_until_complete(self.get_messages(self.entity_id, start_time, end_time))

    def show_message_box(self, title, message):
        msg = QMessageBox()
        msg.setWindowIcon(QtGui.QIcon(GUI_DIR + '/TelegramFxBacktest.png'))
        msg.setBaseSize(QtCore.QSize(300, 130))
        msg.setWindowTitle(title)
        msg.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
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
            each_chat = dict(category=categories[cat_number], chat_name=chat.name, chat_id=chat_id)
            print(each_chat)
            self.chat_list.append(each_chat)

    async def get_messages(self, entity_id, start_time, end_time):
        entity = await client.get_entity(entity_id)
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
            writer.writerow(["Message", "Date"])
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
                    text = ''
                    if start_time <= message.date <= end_time:
                        print(message)
                        if message.message is not None and not message.message == '':
                            text = message.message
                            if message.reply_to_msg_id is not None and message.reply_to_msg_id > 0:
                                for message1 in messages:
                                    if message1.id == message.reply_to_msg_id:
                                        reply_msg = message1.message
                                        break
                                text = text + '\n/////Reply Message////\n' + reply_msg
                        if message.media is not None:
                            if 'MessageMediaDocument' not in str(type(message.media)) and 'MessageMediaPhoto' not in str(type(message.media)):
                                continue
                            if 'MessageMediaDocument' in str(type(message.media)):
                                if message.media.document.mime_type not in ['image/jpeg', 'image/png', 'image/bmp', 'image/gif']:
                                    continue
                            download_path = await client.download_media(
                                message.media, MEDIA_DIR
                            )
                            try:
                                text = text + '\n///////Image//////\n' + tess.image_to_string(Image.open(download_path))
                            except Exception as e:
                                self.show_message_box("Error", "No Tesseract")
                        row = [text, message.date.strftime("%Y-%m-%d %H:%M:%S")]
                        writer.writerow(row)
                offset_id = messages[len(messages) - 1].id
        self.show_message_box("Success", "Code of the backtest : "+code)
        return


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainUI()
    # app.setStyleSheet('QMainWindow{background-image: url(./gui/background.jpg); background-repeat:no-repeat;}')
    window.show()
    app.exec_()
