import pytest
from unittest.mock import MagicMock, patch
from selenium.common.exceptions import TimeoutException
from whatsapp_sender.core.bot import WhatsAppBot

@pytest.fixture
def mock_driver():
    """Fixture for a mocked Selenium WebDriver."""
    return MagicMock()

@pytest.fixture
def bot(mock_driver):
    """Fixture for a WhatsAppBot instance with a mocked driver."""
    return WhatsAppBot(driver=mock_driver)

def test_close(bot, mock_driver):
    """Test that the close method calls the driver's close method."""
    bot.close()
    mock_driver.close.assert_called_once()

def test_check_number_invalid_is_invalid(bot, mocker):
    """Test _check_number_invalid when the number is invalid."""
    mocker.patch('selenium.webdriver.support.ui.WebDriverWait.until', return_value=True)
    assert bot._check_number_invalid("123") is True

def test_check_number_invalid_is_valid(bot, mocker):
    """Test _check_number_invalid when the number is valid."""
    mocker.patch('selenium.webdriver.support.ui.WebDriverWait.until', side_effect=TimeoutException)
    assert bot._check_number_invalid("123") is False

def test_is_message_in_chat_is_present(bot, mocker):
    """Test _is_message_in_chat when the message is found."""
    mock_element = MagicMock()
    mock_element.get_attribute.return_value = "Hello"
    mocker.patch('selenium.webdriver.support.ui.WebDriverWait.until', return_value=mock_element)
    assert bot._is_message_in_chat("Hello") is True

def test_is_message_in_chat_is_not_present(bot, mocker):
    """Test _is_message_in_chat when the message is not found."""
    mocker.patch('selenium.webdriver.support.ui.WebDriverWait.until', side_effect=TimeoutException)
    assert bot._is_message_in_chat("Hello") is False

# Tests for login
@patch('whatsapp_sender.core.bot.WebDriverWait')
def test_login_success(mock_webdriverwait, bot, mock_driver, mocker):
    """Test the successful login flow."""
    mock_wait_instance = MagicMock()
    mock_webdriverwait.return_value = mock_wait_instance
    qr_element_mock = MagicMock()
    mock_wait_instance.until.side_effect = [
        qr_element_mock,
        True,
        MagicMock()
    ]
    mocker.patch('rich.prompt.Prompt.ask')
    bot.login()
    mock_driver.get.assert_called_once_with('https://web.whatsapp.com')
    assert mock_wait_instance.until.call_count == 3

@patch('whatsapp_sender.core.bot.WebDriverWait')
def test_login_already_logged_in(mock_webdriverwait, bot, mock_driver, mocker):
    """Test the flow when the user is already logged in (QR code wait times out)."""
    mock_wait_instance = MagicMock()
    mock_webdriverwait.return_value = mock_wait_instance
    mock_wait_instance.until.side_effect = [
        TimeoutException(),
        MagicMock()
    ]
    mocker.patch('rich.prompt.Prompt.ask')
    bot.login()
    mock_driver.get.assert_called_once_with('https://web.whatsapp.com')
    assert mock_wait_instance.until.call_count == 2

@patch('whatsapp_sender.core.bot.WebDriverWait')
def test_login_main_page_fails_to_load(mock_webdriverwait, bot, mock_driver, mocker):
    """Test login when the main WhatsApp page fails to load."""
    mock_wait_instance = MagicMock()
    mock_webdriverwait.return_value = mock_wait_instance
    qr_element_mock = MagicMock()
    mock_wait_instance.until.side_effect = [
        qr_element_mock,
        True,
        TimeoutException()
    ]
    mocker.patch('rich.prompt.Prompt.ask')
    bot.login()
    mock_driver.get.assert_called_once_with('https://web.whatsapp.com')
    assert mock_wait_instance.until.call_count == 3

# Tests for send_message
@patch('whatsapp_sender.core.bot.add_country_code', return_value="+12345")
@patch('whatsapp_sender.core.bot.quote', return_value="Hello%20World")
@patch('whatsapp_sender.core.bot.append_numbers_to_list')
@patch('time.sleep')
def test_send_message_success(mock_sleep, mock_append, mock_quote, mock_add_country_code, bot, mock_driver, mocker):
    """Test successful message sending on the first attempt."""
    mocker.patch.object(bot, '_check_number_invalid', return_value=False)
    mocker.patch.object(bot, '_is_message_in_chat', side_effect=[False, True])
    mock_wait = mocker.patch('selenium.webdriver.support.ui.WebDriverWait.until')
    mock_wait.return_value.click.return_value = None
    result = bot.send_message("12345", "Hello World")
    assert result is True
    assert mock_driver.get.call_count == 1
    mock_append.assert_not_called()

def test_send_message_invalid_number(bot, mocker):
    """Test send_message when the number is invalid."""
    mocker.patch.object(bot, '_check_number_invalid', return_value=True)
    mock_append = mocker.patch('whatsapp_sender.core.bot.append_numbers_to_list')
    result = bot.send_message("invalid", "message")
    assert result is False
    mock_append.assert_called_once()

def test_send_message_already_in_chat(bot, mocker):
    """Test send_message when the message is already in the chat."""
    mocker.patch.object(bot, '_check_number_invalid', return_value=False)
    mocker.patch.object(bot, '_is_message_in_chat', return_value=True)
    mock_wait = mocker.patch('selenium.webdriver.support.ui.WebDriverWait.until')
    result = bot.send_message("12345", "message")
    assert result is True
    mock_wait.assert_not_called()

@patch('time.sleep')
def test_send_message_fails_all_attempts(mock_sleep, bot, mock_driver, mocker):
    """Test send_message when it fails after all retry attempts."""
    mocker.patch.object(bot, '_check_number_invalid', return_value=False)
    mocker.patch.object(bot, '_is_message_in_chat', return_value=False)
    mocker.patch('selenium.webdriver.support.ui.WebDriverWait.until', side_effect=TimeoutException)
    mock_append = mocker.patch('whatsapp_sender.core.bot.append_numbers_to_list')
    result = bot.send_message("12345", "message")
    assert result is False
    assert mock_driver.get.call_count == 3
    mock_append.assert_called_once()

@patch('time.sleep')
def test_send_message_exception_after_click(mock_sleep, bot, mock_driver, mocker):
    """Test when an exception occurs after clicking send."""
    mocker.patch.object(bot, '_check_number_invalid', return_value=False)
    # This side effect will be consumed by the 3 attempts in the send_message loop
    mocker.patch.object(bot, '_is_message_in_chat', side_effect=[False, Exception("E1"), False, Exception("E2"), False, Exception("E3")])
    mocker.patch('selenium.webdriver.support.ui.WebDriverWait.until')
    mock_append = mocker.patch('whatsapp_sender.core.bot.append_numbers_to_list')

    result = bot.send_message("12345", "message")

    assert result is False
    assert mock_append.call_count == 1

def test_send_message_empty_number(bot):
    """Test send_message with an empty number string."""
    result = bot.send_message(" ", "message")
    assert result is False
