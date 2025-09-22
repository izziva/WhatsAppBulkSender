import logging
from rich import print

from whatsapp_sender.provider.data_manager import read_message, read_numbers, save_numbers, check_number_invalid, append_numbers_to_list
from whatsapp_sender.utils.driver_utils import create_driver
from whatsapp_sender.core.bot import WhatsAppBot
from whatsapp_sender.utils.common_utils import wait_until_work_time
from whatsapp_sender.core.config import settings

def run_cli():
    logger: logging.Logger = logging.getLogger(__name__)
    logger.info = print
    """Function to run the WhatsApp bot in CLI mode."""
    logger.info("[blue]**********************************************************[/blue]")
    logger.info("[blue]************          WhatsApp Automation Tool             ************[/blue]")
    logger.info("[blue]**********************************************************[/blue]")

    message = read_message()
    if not message.strip():
        logger.info("[red]Message is empty. Exiting program.[/red]")
        return

    numbers_to_send = read_numbers(settings.NUMBERS_FILE)
    total_numbers = len(numbers_to_send)
    logger.info(f"[green]Loaded {total_numbers} numbers to process.[/green]")

    remaining_numbers = numbers_to_send.copy()

    driver = None
    try:
        driver = create_driver()
        bot = WhatsAppBot(driver)

        bot.login()

        for idx, number in enumerate(numbers_to_send):
            wait_until_work_time(None, logger)

            logger.info(f"\n[cyan]Processing {idx + 1}/{total_numbers}: {number}[/cyan]")

            if check_number_invalid(number):
                logger.info(f"[yellow]Number {number} is invalid. Saving to not WhatsApp numbers list.[/yellow]")
                append_numbers_to_list(settings.NOT_WAT_NUMBERS_FILE, [number])
                if number in remaining_numbers:
                    remaining_numbers.remove(number)
                save_numbers(settings.NUMBERS_FILE, remaining_numbers)
                continue

            if not bot.send_message(number, message):
                logger.info(f"[red]Could not send message to {number}. It will be retried next session.[/red]")

            if number in remaining_numbers:
                remaining_numbers.remove(number)

            save_numbers(settings.NUMBERS_FILE, remaining_numbers)

        logger.info("[green]\nAll numbers have been processed.[/green]")

    except Exception as e:
        logger.info(f"[bold red]\nAn unexpected error occurred: {e}[/bold red]")
    finally:
        if 'bot' in locals() and bot.driver:
            bot.close()
        if 'remaining_numbers' in locals():
            save_numbers(settings.NUMBERS_FILE, remaining_numbers)
        logger.info("[blue]Program finished.[/blue]")
