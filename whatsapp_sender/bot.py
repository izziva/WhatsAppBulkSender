import logging
import threading
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from urllib.parse import quote
from time import sleep
import random
from rich import print
from rich.prompt import Prompt
import re
from whatsapp_sender.config import settings
from whatsapp_sender.utils import add_country_code, remove_emoji
from whatsapp_sender.data_manager import save_numbers

class WhatsAppBot:
    """A class to automate sending messages on WhatsApp Web."""

    def __init__(self, driver: WebDriver, logger: logging.Logger = None, stop_event: threading.Event = None):
        self.driver = driver
        self.logger = logger or logging.getLogger(__name__)
        self.stop_event = stop_event or threading.Event()
        # Fallback to rich print if no logger is provided (for CLI mode)
        if not logger:
            self.logger.info = print
            self.logger.warning = lambda msg: print(f"[yellow]{msg}[/yellow]")
            self.logger.error = lambda msg: print(f"[red]{msg}[/red]")


    def _check_number_invalid(self, number: str) -> bool:
        """Checks if WhatsApp shows an 'invalid number' dialog and saves it."""
        try:
            WebDriverWait(self.driver, timeout=5, poll_frequency=0.5).until(
                EC.presence_of_element_located((By.XPATH, settings.INVALID_NUMBER_XPATH))
            )
            self.logger.warning(f"Number {number} not registered on WhatsApp. Saving to specific failed list.")
            return True
        except TimeoutException:
            return False

    def _is_message_in_chat(self, message: str) -> bool:
        """Checks if a message with similar content is already in the chat history."""
        try:
            # Pulisce e suddivide il messaggio in parti significative, ignorando emoji e virgolette.
            clean_message = remove_emoji(message).strip()
            parts = [p.strip() for p in re.split(r'\[EMOJI\]|"|\'|\n', clean_message) if p.strip()]

            if not parts:
                return False
            
            xpath_conditions = " and ".join([f"contains(.,'{part}')" for part in parts])
            xpath = f"//div[@role='row']//div/span/span[{xpath_conditions}]"

            WebDriverWait(self.driver, timeout=5, poll_frequency=0.5).until( EC.presence_of_element_located((By.XPATH, xpath)) ).get_attribute("innerText")
            return True
        except TimeoutException:
            return False

    def login(self):
        """Navigates to WhatsApp Web and waits for the user to log in."""
        self.driver.get('https://web.whatsapp.com')
        self.logger.info("Please scan the QR code to log in to WhatsApp Web (if required)...")
        try:
            # Attendi che il QR code appaia, con un timeout breve
            qr_element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, settings.QRCODE_XPATH))
            )
            self.logger.info("Waiting for you to scan the QR code...")
            # Attendi che il QR code scompaia (scansionato o timeout lungo)
            WebDriverWait(self.driver, timeout=settings.LOGIN_TIMEOUT).until(
                EC.staleness_of(qr_element)
            )
        except TimeoutException:
            # Se il QR code non appare o non scompare, potrebbe essere già loggato o c'è un problema
            self.logger.info("QR code not detected or login timeout. Assuming already logged in.")
            pass

        self.logger.info("QR code scanned (or already logged in). Waiting for main page to load...")
        try:
            WebDriverWait(self.driver, timeout=settings.LOGIN_TIMEOUT, poll_frequency=1).until(
                EC.presence_of_element_located((By.ID, "side"))
            )
            self.logger.info("WhatsApp Web loaded successfully.")
        except TimeoutException:
            self.logger.error("Failed to load WhatsApp main page. Please check your connection or log in manually.")
            # Potrebbe essere utile sollevare un'eccezione qui o chiudere
            return


        # In CLI mode, we still want to pause
        if not isinstance(self.logger, logging.Logger):
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
            self.logger.info(f"Attempt {attempt + 1}/3 to send to {number}...")
            self.driver.get(url)

            if self._check_number_invalid(number):
                save_numbers(settings.NOT_WAT_NUMBERS_FILE, [number])
                return False

            if self._is_message_in_chat(message):
                self.logger.info(f"Message already appears to be sent to {number}.")
                sent = True
                return True

            try:
                click_btn = WebDriverWait(self.driver, timeout=settings.DEFAULT_TIMEOUT, poll_frequency=0.5).until(EC.element_to_be_clickable((By.XPATH, settings.SEND_BUTTON_XPATH)))
                click_btn.click()

                if self._is_message_in_chat(message):
                    self.logger.info(f"Message sent successfully to {number}.")
                    sent = True
                    sleep(random.randint(5, 15))
                    break
                else:
                    raise Exception("Message not found in chat after sending.")

            except TimeoutException:
                self.logger.error(f"Timeout while waiting for send button for {number}.")
            except Exception as e:
                self.logger.error(f"Failed to send on attempt {attempt + 1}: {e}")
                if self.stop_event.is_set():
                    self.logger.info("Stop signal received, aborting retries.")
                    break
                sleep(3)
        
        if not sent:
            self.logger.error(f"Failed to send message to {number} after all attempts.")
            save_numbers(settings.FAILED_NUMBERS_FILE, [number])

        return sent

    def close(self):
        """Closes the WebDriver."""
        self.logger.info("Closing the browser.")
        self.driver.close()
