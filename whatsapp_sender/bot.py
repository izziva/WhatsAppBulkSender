from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from urllib.parse import quote
from time import sleep
import random
from rich import print
from rich.prompt import Prompt

from whatsapp_sender.config import DEFAULT_TIMEOUT, LOGIN_TIMEOUT
from whatsapp_sender.utils import remove_emoji, add_country_code


class WhatsAppBot:
    """A class to automate sending messages on WhatsApp Web."""

    def __init__(self, driver: WebDriver):
        self.driver = driver

    def _check_number_invalid(self) -> bool:
        """Checks if WhatsApp shows an 'invalid number' dialog."""
        try:
            WebDriverWait(self.driver, timeout=5, poll_frequency=0.5).until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'URL non valido')] | //div[contains(text(), 'numero di telefono non è su WhatsApp')]"))
            )
            print("[red]Number not registered on WhatsApp.[/red]")
            return True
        except Exception:
            return False

    def _is_message_in_chat(self, message: str) -> bool:
        """Checks if a message with similar content is already in the chat history."""
        try:
            meaningful_text = remove_emoji(message).strip().splitlines()
            meaningful_text = [line for line in meaningful_text if len(line) > 10]
            if not meaningful_text:
                return False

            xpath = f"//span/span[contains(text(), \"{meaningful_text[0][:30]}\")]"
            WebDriverWait(self.driver, timeout=5, poll_frequency=0.5).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
            return True
        except Exception:
            return False

    def login(self):
        """Navigates to WhatsApp Web and waits for the user to log in."""
        self.driver.get('https://web.whatsapp.com')
        print("[magenta]Please scan the QR code to log in to WhatsApp Web...[/magenta]")
        try:
            WebDriverWait(self.driver, timeout=LOGIN_TIMEOUT, poll_frequency=1).until(
                EC.presence_of_element_located((By.XPATH, "//canvas[@aria-label='Scan me!']"))
            )
            print("[yellow]Waiting for you to scan the QR code...[/yellow]")
            WebDriverWait(self.driver, timeout=LOGIN_TIMEOUT, poll_frequency=1).until_not(
                EC.presence_of_element_located((By.XPATH, "//canvas[@aria-label='Scan me!']"))
            )
        except Exception:
            pass

        print("[green]QR code scanned (or already logged in). Waiting for main page to load...[/green]")
        WebDriverWait(self.driver, timeout=LOGIN_TIMEOUT, poll_frequency=1).until(
            EC.presence_of_element_located((By.ID, "side"))
        )
        print("[green]WhatsApp Web loaded successfully.[/green]")
        Prompt.ask("[bold]Press Enter to continue...[/bold]")

    def send_message(self, number: str, message: str) -> bool:
        """Sends a message to a given number."""
        number = number.strip()
        if not number:
            return False

        formatted_number = add_country_code(number)
        url = f"https://web.whatsapp.com/send?phone={formatted_number}&text={quote(message)}"

        sent = False
        for attempt in range(3):
            print(f"[yellow]Attempt {attempt + 1}/3 to send to {number}...[/yellow]")
            self.driver.get(url)

            if self._check_number_invalid():
                return False

            if self._is_message_in_chat(message):
                print(f"[green]Message already appears to be sent to {number}.[/green]")
                return True

            try:
                send_button_xpath = "//button[.//span[@data-icon='send']]"
                click_btn = WebDriverWait(self.driver, timeout=DEFAULT_TIMEOUT, poll_frequency=0.5).until(
                    EC.element_to_be_clickable((By.XPATH, send_button_xpath))
                )
                click_btn.click()
                sleep(2)

                if self._is_message_in_chat(message):
                    print(f"[green]Message sent successfully to {number}.[/green]")
                    sent = True
                    sleep(random.randint(5, 15))
                    break
                else:
                    raise Exception("Message not found in chat after sending.")

            except Exception as e:
                print(f"[red]Failed to send on attempt {attempt + 1}: {e}[/red]")
                sleep(3)

        return sent

    def close(self):
        """Closes the WebDriver."""
        print("[blue]Closing the browser.[/blue]")
        self.driver.close()
