import re
from whatsapp_sender.config import settings
import datetime
from time import sleep
from rich import print
from whatsapp_sender.data_manager import read_numbers

def get_failed_counts() -> tuple[int, int]:
    """
    Counts the number of lines in the failed_numbers.txt and not_whatsapp_numbers.txt files.

    Returns:
        A tuple containing the count of failed numbers and not-WhatsApp numbers.
    """
    failed_count = 0
    not_whatsapp_count = 0

    try:
            failed_count = len(read_numbers(settings.FAILED_NUMBERS_FILE, gui_mode=True))
    except FileNotFoundError:
        pass  # File doesn't exist, count is 0

    try:
            not_whatsapp_count = len(read_numbers(settings.NOT_WAT_NUMBERS_FILE, gui_mode=True))
    except FileNotFoundError:
        pass  # File doesn't exist, count is 0

    return failed_count, not_whatsapp_count

def remove_emoji(text: str) -> str:
    """Removes emoji characters from a string and replaces them with a placeholder string."""
    emoji_pattern = re.compile(
        "["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "]+",
        flags=re.UNICODE,
    )
    return emoji_pattern.sub(r'[EMOJI]', text)

def wait_until_work_time() -> None:
    """Pauses script execution if outside of defined working hours."""
    if not settings.USE_WORK_HOUR_BLOCK:
        return
    now = datetime.datetime.now()
    while now.hour >= settings.WORK_END_HOUR or now.hour < settings.WORK_START_HOUR:
        print(
            f"[red]It is not allowed to send messages after {settings.WORK_END_HOUR}:00 and before {settings.WORK_START_HOUR}:00. "
            "Waiting for unlock...[/red]"
        )
        sleep(600)
        now = datetime.datetime.now()

def add_country_code(number: str) -> str:
    """Formats a phone number to include the Italian country code +39."""
    number = number.strip()
    if number.startswith("+"):
        return number
    elif number.startswith("3"):
        return "+39" + number
    elif number.startswith("00"):
        return "+" + number[2:]
    else:
        print(f"[yellow]Number '{number}' seems to be in a local format. Adding +39 prefix.[/yellow]")
        return "+39" + number


