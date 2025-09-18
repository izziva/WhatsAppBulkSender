import os
import re
from pathlib import Path
from rich import print
from rich.prompt import Prompt
from whatsapp_sender.config import settings

def _load_numbers_from_db() -> list[str]:
    """Loads phone numbers from an Access (.mdb) database file."""
    if not os.path.exists(settings.DB_FILE):
        print(f"[red]Database file not found at: {settings.DB_FILE}[/red]")
        return []

    try:
        import jaydebeapi
    except ImportError:
        print("[red]Module 'jaydebeapi' is not installed. Cannot read from database.[/red]")
        print("[yellow]Please install it via: pip install jaydebeapi[/yellow]")
        return []

    def get_jars():
        lib_dir = Path(settings.LIB_DIR)
        if not lib_dir.exists():
            print(f"[red]JDBC driver directory not found at: {settings.LIB_DIR}[/red]")
            return []
        return [str(jar) for jar in lib_dir.glob("*.jar")]

    jars = get_jars()
    if not jars:
        print("[red]No .jar files found in 'lib' directory for JDBC connection.[/red]")
        return []

    def clean_number(num_str):
        return num_str.replace(" ", "") if num_str else ""

    numbers = list()
    try:
        conn = jaydebeapi.connect(
            jclassname="net.ucanaccess.jdbc.UcanaccessDriver",
            url=f"jdbc:ucanaccess://{settings.DB_FILE}",
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
                    numbers.append(num)
                    break
    except Exception as e:
        print(f"[red]Failed to connect to or read from database: {e}[/red]")
    finally:
        if 'conn' in locals() and conn:
            cursor.close()
            conn.close()

    for num in read_numbers(settings.NOT_WAT_NUMBERS_FILE, gui_mode=True):
        while num in numbers:
            numbers.remove(num)
    return numbers

def read_message(gui_mode: bool = False) -> str:
    """Reads message from file or user input, and caches it."""
    if os.path.exists(settings.MESSAGE_FILE):
        with open(settings.MESSAGE_FILE, "r", encoding="utf8") as file:
            message = file.read()
        if not gui_mode:
            print("[yellow]\nThis is your message:[/yellow]")
            print(f"[green]{message}[/green]")
            if Prompt.ask("[yellow]Do you want to edit the message?[/yellow]", choices=["y", "n"]) == "y":
                message = read_multiline("Please enter your new message (Press Enter twice to finish):")
                save_message(message)
    else:
        message = ""
        if not gui_mode:
            message = read_multiline("Please enter your message (Press Enter twice to finish):")
            save_message(message)
    return message

def save_message(message: str):
    """Saves the message to the file."""
    with open(settings.MESSAGE_FILE, "w", encoding="utf8") as file:
        file.write(message)

def read_numbers(pathFile: str, gui_mode: bool = False) -> list[str]:
    """Reads numbers from a file or loads them from the database."""
    numbers = list()
    if os.path.exists(pathFile):
        with open(pathFile, "r") as file:
            for line in re.split(r',|\n',file.read()):
                num = line.strip()
                if num:
                    numbers.append(num)

    if not gui_mode:
        if not numbers:
            if Prompt.ask("[yellow]No numbers found in 'numbers.txt'. Do you want to load from database?[/yellow]", choices=["y", "n"]) == "y":
                numbers= _load_numbers_from_db()
        else:
            if Prompt.ask(f"[yellow]Found {len(numbers)} numbers from the last session. Continue with these numbers?[/yellow]", choices=["y", "n"]) != "y":
                if Prompt.ask("[yellow]Do you want to reload from database instead?[/yellow]", choices=["y", "n"]) == "y":
                    numbers = _load_numbers_from_db()

        if not numbers:
            print("[red]No numbers to process. Exiting program.[/red]")
            exit()

    return numbers

def save_numbers(pathFile: str, numbers: list[str]) -> None:
    """Saves a list of numbers to the main numbers file."""
    with open(pathFile, "w", encoding="utf-8") as f:
        for number in numbers:
            f.write(f"{number}\n")

def clear_file(file_path: str):
    """Svuota il contenuto di un file."""
    with open(file_path, "w") as f:
        pass

def append_numbers_to_list(pathFile: str,numbers_to_add: list[str]):
    """Aggiunge numeri alla lista principale, evitando duplicati."""
    if not numbers_to_add:
        return
    
    main_numbers = read_numbers(pathFile, gui_mode=True)
    
    # Aggiungi solo numeri non già presenti per evitare duplicati
    unique_new_numbers = [num for num in numbers_to_add if num not in main_numbers]
    
    if not unique_new_numbers:
        return

    updated_numbers = main_numbers + unique_new_numbers
    save_numbers(pathFile, updated_numbers)

def read_multiline(prompt: str) -> str:
    """Reads multiline input from the user until an empty line is entered."""
    print(f"[yellow]{prompt}[/yellow]")
    lines = []
    while True:
        try:
            line = input()
            if line == "" and len(lines)>1 and lines[len(lines) - 1] == "":
                break
            lines.append(line)
        except EOFError:
            break
    return "\n".join(lines)

def check_number_invalid(number: str) -> bool:
    """Checks if a number is invalid by looking for it in the not WhatsApp numbers file."""
    pattern = re.compile("^[0-9\\-\\+]*$")
    return pattern.match(number) is None