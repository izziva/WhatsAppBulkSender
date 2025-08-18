import logging
import threading
from whatsapp_sender.data_manager import read_message, read_numbers, save_numbers
from whatsapp_sender.driver_utils import create_driver
from whatsapp_sender.bot import WhatsAppBot
from whatsapp_sender.utils import wait_until_work_time

def run_bot_instance(logger: logging.Logger, stop_event: threading.Event, post_run_callback: callable):
    """
    This function runs the core bot logic.
    It's designed to be executed in a separate thread from the GUI.
    """
    logger.info("Bot instance started.")

    try:
        message = read_message(gui_mode=True)
        if not message.strip():
            logger.warning("Message is empty. Aborting.")
            return

        numbers_to_send = read_numbers(gui_mode=True)
        total_numbers = len(numbers_to_send)
        logger.info(f"Loaded {total_numbers} numbers to process.")

        remaining_numbers = numbers_to_send.copy()

        driver = None
        bot = None
        try:
            driver = create_driver()
            bot = WhatsAppBot(driver, logger=logger, stop_event=stop_event)

            bot.login()
            if stop_event.is_set():
                raise Exception("Stop signal received during login.")

            for idx, number in enumerate(numbers_to_send):
                if stop_event.is_set():
                    logger.info("Stop signal received. Halting message sending.")
                    break

                wait_until_work_time()
                if stop_event.is_set(): break

                logger.info(f"Processing {idx + 1}/{total_numbers}: {number}")

                success = bot.send_message(number, message)

                if success:
                    if number in remaining_numbers:
                        remaining_numbers.remove(number)
                else:
                    logger.warning(f"Could not send message to {number}. It will be retried next session.")

                save_numbers(remaining_numbers)

            logger.info("All numbers have been processed or the process was stopped.")

        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
        finally:
            if bot and bot.driver:
                bot.close()
            if 'remaining_numbers' in locals():
                save_numbers(remaining_numbers)
            logger.info("Bot instance finished.")
    finally:
        # This will be called even if the bot logic fails catastrophically
        post_run_callback()
