import os
import json

# PATHS
_cur_dir = os.path.dirname(os.path.realpath(__file__))
ROOT_DIR = os.path.join(_cur_dir, os.pardir)
LOG_DIR = os.path.join(ROOT_DIR, 'logs')
CRED_DIR = os.path.join(ROOT_DIR, 'credentials')
GUI_DIR = os.path.join(ROOT_DIR, 'gui')
CSV_DIR = os.path.join(ROOT_DIR, 'csv')
MEDIA_DIR = os.path.join(ROOT_DIR, 'media')
credential_file = "config.ini"
gui_file = "telegram_client.ui"

