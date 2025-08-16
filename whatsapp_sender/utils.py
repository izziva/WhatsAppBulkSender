import re
import datetime
from time import sleep
from rich import print
from whatsapp_sender.config import WORK_START_HOUR, WORK_END_HOUR

def remove_emoji(text: str) -> str:
    """Removes emoji characters from a string."""
    emoji_pattern = re.compile(
        "["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "]+",
        flags=re.UNICODE,
    )
    return emoji_pattern.sub(r'', text)

def wait_until_work_time() -> None:
    """Pauses script execution if outside of defined working hours."""
    now = datetime.datetime.now()
    while now.hour >= WORK_END_HOUR or now.hour < WORK_START_HOUR:
        print(
            f"[red]It is not allowed to send messages after {WORK_END_HOUR}:00 and before {WORK_START_HOUR}:00. "
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

def read_multiline(prompt: str) -> str:
    """Reads multiline input from the user until an empty line is entered."""
    print(f"[yellow]{prompt}[/yellow]")
    lines = []
    while True:
        try:
            line = input()
            if line == "":
                break
            lines.append(line)
        except EOFError:
            break
    return "\n".join(lines)
