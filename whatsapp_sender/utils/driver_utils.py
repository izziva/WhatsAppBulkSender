import os
from rich import print
from selenium.webdriver.chrome.webdriver import WebDriver as Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from whatsapp_sender.core.config import settings

def create_driver() -> Chrome:
    """Initializes and returns a configured Selenium Chrome WebDriver."""
    options = Options()
    # Suppress webdriver manager logs
    os.environ["WDM_LOG_LEVEL"] = "0"

    # Experimental options and arguments for stability and ad-blocking
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    options.add_argument("--profile-directory=Default")
    options.add_argument("--user-data-dir=" + settings.USER_DATA_DIR)
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--disable-web-security")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-notifications")

    # Use a try-except block for robustness in service creation
    try:
        service = Service(ChromeDriverManager().install())
        driver = Chrome(service=service, options=options)
    except Exception as e:
        print(f"[bold red]Error creating WebDriver: {e}[/bold red]")
        # Fallback or specific error handling can be added here
        raise

    return driver
