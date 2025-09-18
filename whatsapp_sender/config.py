from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    # --- File and Path Constants ---
    # Use absolute paths to ensure the script runs from any directory
    CWD: str = os.getcwd()
    MESSAGE_FILE: str = os.path.join(CWD, "message.txt")
    NUMBERS_FILE: str = os.path.join(CWD, "numbers.txt")
    FAILED_NUMBERS_FILE: str = os.path.join(CWD, "failed_numbers.txt")
    NOT_WAT_NUMBERS_FILE: str = os.path.join(CWD, "not_whatsapp_numbers.txt")
    DB_FILE: str = os.path.join(CWD, "archivio.mdb")
    USER_DATA_DIR: str = os.path.join(CWD, "whatsappProfile/")
    LIB_DIR: str = os.path.join(CWD, "lib")

    # --- Selenium Constants ---
    DEFAULT_TIMEOUT: int = 20
    CHECK_NUMBER_TIMEOUT: int = 10
    LOGIN_TIMEOUT: int = 80

    # --- Operational Constants ---
    USE_WORK_HOUR_BLOCK: bool = True 
    WORK_START_HOUR: int = 9
    WORK_END_HOUR: int = 22

    QRCODE_XPATH: str = "//canvas[@aria-label='Scan me!']"
    INVALID_NUMBER_XPATH: str = "//div[@role='dialog']//div/button//div[contains(text(),'OK')] | //div[contains(text(), 'numero di telefono non è su WhatsApp')]"
    SEND_BUTTON_XPATH: str = "//button[.//span[contains(@data-icon, 'send')]]"
    MESSAGE_IN_CHAT_XPATH: str = "//div[@role='row']//div/span[{conditions}]" 

settings = Settings()
