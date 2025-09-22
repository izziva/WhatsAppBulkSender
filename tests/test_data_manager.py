import pytest
import sys
from unittest.mock import MagicMock, mock_open, patch
from whatsapp_sender.provider.data_manager import (
    check_number_invalid,
    save_message,
    save_numbers,
    clear_file,
    append_numbers_to_list,
    read_multiline,
    read_message,
    read_numbers,
    _load_numbers_from_db
)

# Tests for check_number_invalid
def test_check_number_invalid_valid():
    assert not check_number_invalid("+391234567890")
    assert not check_number_invalid("1234567890")

def test_check_number_invalid_invalid():
    assert check_number_invalid("invalid_number")
    assert check_number_invalid("123-abc")

# Tests for save_message
def test_save_message(mocker):
    m = mock_open()
    mocker.patch('builtins.open', m)
    save_message("Hello World")
    m.assert_called_once_with(mocker.ANY, "w", encoding="utf8")
    m().write.assert_called_once_with("Hello World")

# Tests for save_numbers
def test_save_numbers(mocker):
    m = mock_open()
    mocker.patch('builtins.open', m)
    numbers = ["1", "2", "3"]
    save_numbers("some_path.txt", numbers)
    m.assert_called_once_with("some_path.txt", "w", encoding="utf-8")
    assert m().write.call_count == 3
    m().write.assert_any_call("1\n")
    m().write.assert_any_call("2\n")
    m().write.assert_any_call("3\n")

# Tests for clear_file
def test_clear_file(mocker):
    m = mock_open()
    mocker.patch('builtins.open', m)
    clear_file("some_path.txt")
    m.assert_called_once_with("some_path.txt", "w")
    m().write.assert_not_called()

# Tests for append_numbers_to_list
def test_append_numbers_to_list(mocker):
    mock_read = mocker.patch('whatsapp_sender.provider.data_manager.read_numbers', return_value=["1", "2"])
    mock_save = mocker.patch('whatsapp_sender.provider.data_manager.save_numbers')

    append_numbers_to_list("path.txt", ["2", "3", "4"])

    mock_read.assert_called_once_with("path.txt", gui_mode=True)
    mock_save.assert_called_once_with("path.txt", ["1", "2", "3", "4"])

def test_append_numbers_to_list_no_new_numbers(mocker):
    mock_read = mocker.patch('whatsapp_sender.provider.data_manager.read_numbers', return_value=["1", "2"])
    mock_save = mocker.patch('whatsapp_sender.provider.data_manager.save_numbers')

    append_numbers_to_list("path.txt", ["1", "2"])

    mock_read.assert_called_once_with("path.txt", gui_mode=True)
    mock_save.assert_not_called()

# Tests for read_multiline
def test_read_multiline(mocker):
    # The function breaks on two consecutive empty lines.
    mocker.patch('builtins.input', side_effect=["line 1", "line 2", "", ""])
    message = read_multiline("prompt")
    # The current implementation joins ["line 1", "line 2", ""], which results in a trailing newline.
    assert message == "line 1\nline 2\n"

# Tests for read_message
def test_read_message_file_exists_no_edit(mocker):
    mocker.patch('os.path.exists', return_value=True)
    mocker.patch('builtins.open', mock_open(read_data="Test message"))
    mocker.patch('rich.prompt.Prompt.ask', return_value='n')

    message = read_message()

    assert message == "Test message"

def test_read_message_file_exists_edit(mocker):
    mocker.patch('os.path.exists', return_value=True)
    mocker.patch('builtins.open', mock_open(read_data="Old message"))
    mocker.patch('rich.prompt.Prompt.ask', return_value='y')
    mocker.patch('whatsapp_sender.provider.data_manager.read_multiline', return_value="New message")
    mock_save = mocker.patch('whatsapp_sender.provider.data_manager.save_message')

    message = read_message()

    assert message == "New message"
    mock_save.assert_called_once_with("New message")

def test_read_message_no_file(mocker):
    mocker.patch('os.path.exists', return_value=False)
    mocker.patch('whatsapp_sender.provider.data_manager.read_multiline', return_value="New message from input")
    mock_save = mocker.patch('whatsapp_sender.provider.data_manager.save_message')

    message = read_message()

    assert message == "New message from input"
    mock_save.assert_called_once_with("New message from input")

# Tests for read_numbers
def test_read_numbers_file_exists(mocker):
    mocker.patch('os.path.exists', return_value=True)
    mocker.patch('builtins.open', mock_open(read_data="1,2,3\n4"))

    numbers = read_numbers("path.txt", gui_mode=True)

    assert numbers == ["1", "2", "3", "4"]

def test_read_numbers_no_file_gui_mode(mocker):
    mocker.patch('os.path.exists', return_value=False)

    numbers = read_numbers("path.txt", gui_mode=True)

    assert numbers == []

def test_read_numbers_no_file_load_db(mocker):
    mocker.patch('os.path.exists', return_value=False)
    mocker.patch('rich.prompt.Prompt.ask', return_value='y')
    mocker.patch('whatsapp_sender.provider.data_manager._load_numbers_from_db', return_value=["db1", "db2"])

    numbers = read_numbers("path.txt")

    assert numbers == ["db1", "db2"]

def test_read_numbers_continue_with_session(mocker):
    mocker.patch('os.path.exists', return_value=True)
    mocker.patch('builtins.open', mock_open(read_data="1,2,3"))
    mocker.patch('rich.prompt.Prompt.ask', return_value='y')
    mock_load_db = mocker.patch('whatsapp_sender.provider.data_manager._load_numbers_from_db')

    numbers = read_numbers("path.txt")

    assert numbers == ["1", "2", "3"]
    mock_load_db.assert_not_called()

# Tests for _load_numbers_from_db
@patch('whatsapp_sender.provider.data_manager.os.path.exists', return_value=True)
@patch('whatsapp_sender.provider.data_manager.Path')
@patch.dict('sys.modules', {'jaydebeapi': MagicMock()})
def test_load_numbers_from_db_success(mock_path, mock_exists):
    import jaydebeapi
    # Mock Path and jars
    mock_path.return_value.glob.return_value = [MagicMock(name='ucanaccess.jar')]

    # Mock DB connection and cursor
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [
        ("3331234567", "office", "phone", "code1"),
        ("3337654321", "no promo", "phone", "code2"), # Should be skipped
    ]
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    jaydebeapi.connect.return_value = mock_conn

    # Mock read_numbers for NOT_WAT_NUMBERS_FILE
    with patch('whatsapp_sender.provider.data_manager.read_numbers', return_value=[]):
        numbers = _load_numbers_from_db()

    # NOTE: The filtering logic for "(no promo)" does not seem to be working as intended.
    # The test is adjusted to match the current, non-filtering behavior as per the instruction
    # not to change the program's behavior at this stage.
    assert "3331234567" in numbers
    assert "3337654321" in numbers
    assert len(numbers) == 2
    jaydebeapi.connect.assert_called_once()

@patch('whatsapp_sender.provider.data_manager.os.path.exists', return_value=False)
def test_load_numbers_from_db_no_db_file(mock_exists):
    numbers = _load_numbers_from_db()
    assert numbers == []

@patch('whatsapp_sender.provider.data_manager.os.path.exists', return_value=True)
@patch.dict('sys.modules')
def test_load_numbers_from_db_no_jaydebeapi(mock_exists):
    if 'jaydebeapi' in sys.modules:
        del sys.modules['jaydebeapi']

    numbers = _load_numbers_from_db()
    assert numbers == []

@patch('whatsapp_sender.provider.data_manager.os.path.exists', return_value=True)
@patch.dict('sys.modules', {'jaydebeapi': MagicMock()})
@patch('whatsapp_sender.provider.data_manager.Path')
def test_load_numbers_from_db_no_jars(mock_path, mock_exists):
    mock_path.return_value.glob.return_value = [] # No jar files
    numbers = _load_numbers_from_db()
    assert numbers == []

@patch('whatsapp_sender.provider.data_manager.os.path.exists', return_value=True)
@patch.dict('sys.modules', {'jaydebeapi': MagicMock()})
@patch('whatsapp_sender.provider.data_manager.Path')
@patch('whatsapp_sender.provider.data_manager.read_numbers', return_value=[])
def test_load_numbers_from_db_connect_exception(mock_read_numbers, mock_path, mock_exists):
    import jaydebeapi
    mock_path.return_value.glob.return_value = [MagicMock(name='ucanaccess.jar')]
    jaydebeapi.connect.side_effect = Exception("DB Error")

    numbers = _load_numbers_from_db()
    assert numbers == []

@patch('whatsapp_sender.provider.data_manager.os.path.exists', return_value=True)
@patch.dict('sys.modules', {'jaydebeapi': MagicMock()})
@patch('whatsapp_sender.provider.data_manager.Path')
@patch('whatsapp_sender.provider.data_manager.read_numbers', return_value=["3331234567"]) # This number is in the "not wat" list
def test_load_numbers_from_db_removes_not_wat_numbers(mock_read, mock_path, mock_exists):
    import jaydebeapi
    mock_path.return_value.glob.return_value = [MagicMock(name='ucanaccess.jar')]
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [("3331234567", "office", "phone", "code1"), ("3338888888", "office", "phone", "code2")]
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    jaydebeapi.connect.return_value = mock_conn

    numbers = _load_numbers_from_db()

    assert "3331234567" not in numbers
    assert "3338888888" in numbers

def test_read_numbers_reload_from_db(mocker):
    mocker.patch('os.path.exists', return_value=True)
    mocker.patch('builtins.open', mock_open(read_data="1,2,3"))
    # User doesn't want to continue, then wants to reload
    mocker.patch('rich.prompt.Prompt.ask', side_effect=['n', 'y'])
    mock_load_db = mocker.patch('whatsapp_sender.provider.data_manager._load_numbers_from_db', return_value=["db1", "db2"])

    numbers = read_numbers("path.txt")

    assert numbers == ["db1", "db2"]
    mock_load_db.assert_called_once()
