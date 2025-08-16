import os

# --- File and Path Constants ---
# Use absolute paths to ensure the script runs from any directory
CWD = os.getcwd()
MESSAGE_FILE = os.path.join(CWD, "message.txt")
NUMBERS_FILE = os.path.join(CWD, "numbers.txt")
DB_FILE = os.path.join(CWD, "archivio.mdb")
USER_DATA_DIR = os.path.join(CWD, "watshappProfile/")
LIB_DIR = os.path.join(CWD, "lib")

# --- Selenium Constants ---
DEFAULT_TIMEOUT = 16
# Using a longer timeout for the initial login to allow time for QR code scanning
LOGIN_TIMEOUT = 120

# --- Operational Constants ---
WORK_START_HOUR = 9
WORK_END_HOUR = 22

# The style class has been removed as the project now uses the 'rich' library for terminal styling.
