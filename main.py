import argparse
from rich import print

from whatsapp_sender.data_manager import read_message, read_numbers, save_numbers, check_number_invalid
from whatsapp_sender.driver_utils import create_driver
from whatsapp_sender.bot import WhatsAppBot
from whatsapp_sender.utils import wait_until_work_time
from whatsapp_sender.config import settings

def run_cli():
    """Function to run the WhatsApp bot in CLI mode."""
    print("[blue]**********************************************************[/blue]")
    print("[blue]*****          WhatsApp Automation Tool             ******[/blue]")
    print("[blue]**********************************************************[/blue]")

    message = read_message()
    if not message.strip():
        print("[red]Message is empty. Exiting program.[/red]")
        return

    numbers_to_send = read_numbers(settings.NUMBERS_FILE)
    total_numbers = len(numbers_to_send)
    print(f"[green]Loaded {total_numbers} numbers to process.[/green]")

    remaining_numbers = numbers_to_send.copy()

    driver = None
    try:
        driver = create_driver()
        bot = WhatsAppBot(driver)

        bot.login()

        for idx, number in enumerate(numbers_to_send):
            wait_until_work_time()

            print(f"\n[cyan]Processing {idx + 1}/{total_numbers}: {number}[/cyan]")

            if check_number_invalid(number):
                print(f"[yellow]Number {number} is invalid. Saving to not WhatsApp numbers list.[/yellow]")
                save_numbers(settings.NOT_WAT_NUMBERS_FILE, [number])
                if number in remaining_numbers:
                    remaining_numbers.remove(number)
                save_numbers(settings.NUMBERS_FILE, remaining_numbers)
                continue

            if not bot.send_message(number, message):
                print(f"[red]Could not send message to {number}. It will be retried next session.[/red]")

            if number in remaining_numbers:
                remaining_numbers.remove(number)
            

            save_numbers(settings.NUMBERS_FILE, remaining_numbers)

        print("[green]\nAll numbers have been processed.[/green]")

    except Exception as e:
        print(f"[bold red]\nAn unexpected error occurred: {e}[/bold red]")
    finally:
        if 'bot' in locals() and bot.driver:
            bot.close()
        if 'remaining_numbers' in locals():
            save_numbers(settings.NUMBERS_FILE, remaining_numbers)
        print("[blue]Program finished.[/blue]")

def run_gui():
    """Function to run the WhatsApp bot in GUI mode."""
    from whatsapp_sender.gui import App
    app = App()
    app.mainloop()


def main():
    """Main function to parse arguments and run the bot."""
    parser = argparse.ArgumentParser(description="WhatsApp Automation Tool")
    parser.add_argument(
        "--nogui",
        action="store_true",
        help="Run the application in command-line interface (CLI) mode.",
    )
    args = parser.parse_args()

    if args.nogui:
        run_cli()
    else:
        run_gui()

if __name__ == "__main__":
    main()
