import os
import json

# PATHS
_cur_dir = os.path.dirname(os.path.realpath(__file__))
ROOT_DIR = os.path.join(_cur_dir, os.pardir)
CRED_DIR = os.path.join(ROOT_DIR, 'credentials')
GUI_DIR = os.path.join(ROOT_DIR, 'gui')
CSV_DIR = os.path.join(ROOT_DIR, 'csv')
if not os.path.exists(CSV_DIR):
    os.mkdir(CSV_DIR)
MEDIA_DIR = os.path.join(ROOT_DIR, 'media')
if not os.path.exists(MEDIA_DIR):
    os.mkdir(MEDIA_DIR)
credential_file = "config.ini"
main_ui_file = "main.ui"
telegram_ui_file = "telegram.ui"
login_ui_file = "login.ui"

tesseract_env = os.path.join(ROOT_DIR, 'tesseract') + '/tesseract.exe'

