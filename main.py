from rich import print
from whatsapp_sender.data_manager import read_message, read_numbers, update_numbers_file
from whatsapp_sender.driver_utils import create_driver
from whatsapp_sender.bot import WhatsAppBot
from whatsapp_sender.utils import wait_until_work_time

def main():
    """Main function to run the WhatsApp bot."""
    print("[blue]**********************************************************[/blue]")
    print("[blue]*****      WhatsApp Automation Tool Refactored     ******[/blue]")
    print("[blue]**********************************************************[/blue]")

    message = read_message()
    if not message.strip():
        print("[red]Message is empty. Exiting program.[/red]")
        return

    numbers_to_send = read_numbers()
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

            success = bot.send_message(number, message)

            if success:
                # If sent, remove from the list of numbers to be saved for next time
                if number in remaining_numbers:
                    remaining_numbers.remove(number)
            else:
                print(f"[red]Could not send message to {number}. It will be retried next session.[/red]")

            # Save progress after each attempt
            update_numbers_file(remaining_numbers)

        print("[green]\nAll numbers have been processed.[/green]")

    except Exception as e:
        print(f"[bold red]\nAn unexpected error occurred: {e}[/bold red]")
    finally:
        if 'bot' in locals() and bot.driver:
            bot.close()
        # Final save of remaining numbers
        if 'remaining_numbers' in locals():
            update_numbers_file(remaining_numbers)
        print("[blue]Program finished.[/blue]")

if __name__ == "__main__":
    main()
