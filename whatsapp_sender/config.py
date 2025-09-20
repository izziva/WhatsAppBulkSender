from pydantic_settings import BaseSettings, SettingsConfigDict
import os
import sys

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    # --- File and Path Constants ---
    # Use absolute paths to ensure the script runs from any directory
    CWD: str = os.getcwd()
    MESSAGE_FILE: str = resource_path("message.txt")
    NUMBERS_FILE: str = resource_path("numbers.txt")
    DB_FILE: str = resource_path("archivio.mdb")
    USER_DATA_DIR: str = resource_path("watshappProfile/")
    LIB_DIR: str = resource_path("lib")

    # --- Selenium Constants ---
    DEFAULT_TIMEOUT: int = 16
    LOGIN_TIMEOUT: int = 120

    # --- Operational Constants ---
    WORK_START_HOUR: int = 9
    WORK_END_HOUR: int = 22

settings = Settings()
