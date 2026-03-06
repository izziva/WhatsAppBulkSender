import pytest
from unittest.mock import MagicMock, patch
from whatsapp_sender.console.cli import run_cli

# Tests for run_cli function
@patch('whatsapp_sender.console.cli.read_message', return_value="Test")
@patch('whatsapp_sender.console.cli.read_numbers', return_value=["1", "2"])
@patch('whatsapp_sender.console.cli.save_numbers')
@patch('whatsapp_sender.console.cli.create_driver')
@patch('whatsapp_sender.console.cli.WhatsAppBot')
@patch('whatsapp_sender.console.cli.wait_until_work_time')
@patch('whatsapp_sender.console.cli.check_number_invalid', return_value=False)
@patch('whatsapp_sender.console.cli.append_numbers_to_list')
def test_run_cli_success(mock_append, mock_check_invalid, mock_wait, mock_bot, mock_driver, mock_save, mock_read_numbers, mock_read_message):
    """Test a successful run of the CLI."""
    mock_bot.return_value.send_message.return_value = True

    run_cli()

    mock_read_message.assert_called_once()
    mock_read_numbers.assert_called_once()
    assert mock_bot.return_value.send_message.call_count == 2
    mock_bot.return_value.close.assert_called_once()

@patch('whatsapp_sender.console.cli.read_message', return_value="")
@patch('whatsapp_sender.console.cli.read_numbers')
def test_run_cli_empty_message(mock_read_numbers, mock_read_message):
    """Test that CLI exits if message is empty."""
    run_cli()
    mock_read_numbers.assert_not_called()

@patch('whatsapp_sender.console.cli.read_message', return_value="Test")
@patch('whatsapp_sender.console.cli.read_numbers', return_value=["invalid-number"])
@patch('whatsapp_sender.console.cli.create_driver')
@patch('whatsapp_sender.console.cli.check_number_invalid', return_value=True)
@patch('whatsapp_sender.console.cli.append_numbers_to_list')
def test_run_cli_invalid_number(mock_append, mock_check, mock_driver, mock_read_numbers, mock_read_message, mocker):
    """Test that an invalid number is skipped."""
    mock_bot = mocker.patch('whatsapp_sender.console.cli.WhatsAppBot')
    run_cli()
    mock_append.assert_called_once()
    mock_bot.return_value.send_message.assert_not_called()

@patch('whatsapp_sender.console.cli.read_message', return_value="Test")
@patch('whatsapp_sender.console.cli.read_numbers', return_value=["1"])
@patch('whatsapp_sender.console.cli.create_driver')
@patch('whatsapp_sender.console.cli.check_number_invalid', return_value=False)
def test_run_cli_send_fail(mock_check, mock_driver, mock_read_numbers, mock_read_message, mocker):
    """Test the case where send_message returns False."""
    mock_bot = mocker.patch('whatsapp_sender.console.cli.WhatsAppBot')
    mock_bot.return_value.send_message.return_value = False
    run_cli()
    mock_bot.return_value.send_message.assert_called_once()

@patch('whatsapp_sender.console.cli.read_message', return_value="Test")
@patch('whatsapp_sender.console.cli.read_numbers', return_value=["1"])
@patch('whatsapp_sender.console.cli.create_driver', side_effect=Exception("Test Exception"))
def test_run_cli_exception(mock_driver, mock_read_numbers, mock_read_message):
    """Test that an exception is handled."""
    # Should not raise, just log the error
    run_cli()
