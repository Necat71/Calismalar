# config.py

import sys
from pathlib import Path


def get_base_path():
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS)
    return Path(__file__).parent


BASE_DIR = get_base_path()
DB_FILE = BASE_DIR / "data" / "sirket.db"

UI_PATHS = {
    "poz_selection": BASE_DIR / "ui" / "poz_selection_dialog.ui"
}


def get_config():
    return {
        "UI_PATHS": UI_PATHS,
        "DB_FILE": DB_FILE
    }

