import os
from pathlib import Path
from rich import print
from rich.prompt import Prompt
from whatsapp_sender.config import MESSAGE_FILE, NUMBERS_FILE, DB_FILE, LIB_DIR
from whatsapp_sender.utils import read_multiline

def _load_numbers_from_db() -> list[str]:
    """Loads phone numbers from an Access (.mdb) database file."""
    if not os.path.exists(DB_FILE):
        print(f"[red]Database file not found at: {DB_FILE}[/red]")
        return []

    try:
        import jaydebeapi
    except ImportError:
        print("[red]Module 'jaydebeapi' is not installed. Cannot read from database.[/red]")
        print("[yellow]Please install it via: pip install jaydebeapi[/yellow]")
        return []

    def get_jars():
        lib_dir = Path(LIB_DIR)
        if not lib_dir.exists():
            print(f"[red]JDBC driver directory not found at: {LIB_DIR}[/red]")
            return []
        return [str(jar) for jar in lib_dir.glob("*.jar")]

    jars = get_jars()
    if not jars:
        print("[red]No .jar files found in 'lib' directory for JDBC connection.[/red]")
        return []

    def clean_number(num_str):
        return num_str.replace(" ", "") if num_str else ""

    numbers = set()
    try:
        conn = jaydebeapi.connect(
            jclassname="net.ucanaccess.jdbc.UcanaccessDriver",
            url=f"jdbc:ucanaccess://{DB_FILE}",
            jars=jars,
        )
        cursor = conn.cursor()
        cursor.execute("SELECT tel as MOBILE, cc as UFFICIO, ufficio as TELEFONO, cod FROM clienti;")
        for row in cursor.fetchall():
            mobile, ufficio, telefono = [clean_number(str(col or "").strip()) for col in row[:3]]

            if any("(no promo)" in val for val in row[:3] if val):
                continue

            for num in [mobile, ufficio, telefono]:
                if len(num) > 6 and len(num) <= 12 and num.startswith("3") and num.isdigit():
                    numbers.add(num)
                    break
    except Exception as e:
        print(f"[red]Failed to connect to or read from database: {e}[/red]")
    finally:
        if 'conn' in locals() and conn:
            cursor.close()
            conn.close()

    return list(numbers)

def read_message() -> str:
    """Reads message from file or user input, and caches it."""
    if os.path.exists(MESSAGE_FILE):
        with open(MESSAGE_FILE, "r", encoding="utf8") as file:
            message = file.read()
        print("[yellow]\nThis is your message:[/yellow]")
        print(f"[green]{message}[/green]")
        if Prompt.ask("[yellow]Do you want to edit the message?[/yellow]", choices=["y", "n"]) == "y":
            message = read_multiline("Please enter your new message (Press Enter twice to finish):")
            with open(MESSAGE_FILE, "w", encoding="utf8") as file:
                file.write(message)
    else:
        message = read_multiline("Please enter your message (Press Enter twice to finish):")
        with open(MESSAGE_FILE, "w", encoding="utf8") as file:
            file.write(message)
    return message

def read_numbers() -> list[str]:
    """Reads numbers from a file or loads them from the database."""
    numbers = set()
    if os.path.exists(NUMBERS_FILE):
        with open(NUMBERS_FILE, "r") as file:
            for line in file.read().split(","):
                num = line.strip()
                if num:
                    numbers.add(num)

    if not numbers:
        if Prompt.ask("[yellow]No numbers found in 'numbers.txt'. Do you want to load from database?[/yellow]", choices=["y", "n"]) == "y":
            numbers.update(_load_numbers_from_db())
    else:
        if Prompt.ask(f"[yellow]Found {len(numbers)} numbers from the last session. Continue with these numbers?[/yellow]", choices=["y", "n"]) != "y":
            if Prompt.ask("[yellow]Do you want to reload from database instead?[/yellow]", choices=["y", "n"]) == "y":
                numbers = set(_load_numbers_from_db())

    if not numbers:
        print("[red]No numbers to process. Exiting program.[/red]")
        exit()

    return list(numbers)

def update_numbers_file(numbers_to_send: list[str]):
    """Saves the remaining list of numbers to the file."""
    with open(NUMBERS_FILE, "w") as f:
        f.write(",".join(numbers_to_send))
