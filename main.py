import argparse
from whatsapp_sender import __version__
from whatsapp_sender.core.updater import check_for_updates
from whatsapp_sender.console.cli import run_cli
from whatsapp_sender.gui.app import App

def run_gui():
    """Function to run the WhatsApp bot in GUI mode."""
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

    # Check for updates
    check_for_updates(__version__, gui_mode=not args.nogui)

    if args.nogui:
        run_cli()
    else:
        run_gui()

if __name__ == "__main__":
    main()
