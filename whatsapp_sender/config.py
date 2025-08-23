from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    # --- File and Path Constants ---
    # Use absolute paths to ensure the script runs from any directory
    CWD: str = os.getcwd()
    MESSAGE_FILE: str = os.path.join(CWD, "message.txt")
    NUMBERS_FILE: str = os.path.join(CWD, "numbers.txt")
    DB_FILE: str = os.path.join(CWD, "archivio.mdb")
    USER_DATA_DIR: str = os.path.join(CWD, "watshappProfile/")
    LIB_DIR: str = os.path.join(CWD, "lib")

    # --- Selenium Constants ---
    DEFAULT_TIMEOUT: int = 16
    LOGIN_TIMEOUT: int = 120

    # --- Operational Constants ---
    WORK_START_HOUR: int = 9
    WORK_END_HOUR: int = 22

settings = Settings()
