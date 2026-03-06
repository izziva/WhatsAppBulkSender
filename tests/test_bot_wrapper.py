import pytest
from unittest.mock import MagicMock, patch
from whatsapp_sender.core.bot_wrapper import run_bot_instance

@pytest.fixture
def mock_dependencies(mocker):
    """Fixture to mock all external dependencies of run_bot_instance."""
    mocks = {
        'read_message': mocker.patch('whatsapp_sender.core.bot_wrapper.read_message', return_value="Test Message"),
        'read_numbers': mocker.patch('whatsapp_sender.core.bot_wrapper.read_numbers', return_value=["1", "2"]),
        'save_numbers': mocker.patch('whatsapp_sender.core.bot_wrapper.save_numbers'),
        'create_driver': mocker.patch('whatsapp_sender.core.bot_wrapper.create_driver'),
        'WhatsAppBot': mocker.patch('whatsapp_sender.core.bot_wrapper.WhatsAppBot'),
        'wait_until_work_time': mocker.patch('whatsapp_sender.core.bot_wrapper.wait_until_work_time'),
        'check_number_invalid': mocker.patch('whatsapp_sender.core.bot_wrapper.check_number_invalid', return_value=False),
        'append_numbers_to_list': mocker.patch('whatsapp_sender.core.bot_wrapper.append_numbers_to_list'),
    }
    # Mock the bot's send_message method
    mocks['WhatsAppBot'].return_value.send_message.return_value = True
    return mocks

def test_run_bot_instance_success(mock_dependencies):
    """Test a successful run of the bot instance."""
    logger = MagicMock()
    stop_event = MagicMock()
    stop_event.is_set.return_value = False
    post_run_callback = MagicMock()

    run_bot_instance(logger, stop_event, post_run_callback)

    mock_dependencies['read_message'].assert_called_once()
    mock_dependencies['read_numbers'].assert_called_once()
    assert mock_dependencies['WhatsAppBot'].return_value.send_message.call_count == 2
    mock_dependencies['WhatsAppBot'].return_value.close.assert_called_once()
    post_run_callback.assert_called_once()

def test_run_bot_instance_empty_message(mock_dependencies):
    """Test that the bot aborts if the message is empty."""
    mock_dependencies['read_message'].return_value = " " # Empty after strip

    run_bot_instance(MagicMock(), MagicMock(), MagicMock())

    mock_dependencies['read_numbers'].assert_not_called()
    mock_dependencies['create_driver'].assert_not_called()

def test_run_bot_instance_stop_event_in_loop(mock_dependencies):
    """Test that the bot stops when the stop event is set during the loop."""
    stop_event = MagicMock()
    # is_set calls: after login, before wait (L1), after wait (L1), before wait (L2)
    stop_event.is_set.side_effect = [False, False, False, True]

    run_bot_instance(MagicMock(), stop_event, MagicMock())

    # Should only send one message
    assert mock_dependencies['WhatsAppBot'].return_value.send_message.call_count == 1

@patch('whatsapp_sender.core.bot_wrapper.create_driver', side_effect=Exception("Driver Error"))
def test_run_bot_instance_exception(mock_create_driver, mock_dependencies):
    """Test that the callback is called even if an exception occurs."""
    post_run_callback = MagicMock()

    run_bot_instance(MagicMock(), MagicMock(), post_run_callback)

    post_run_callback.assert_called_once()

def test_run_bot_instance_stop_after_login(mock_dependencies):
    """Test that the bot stops if the stop event is set after login."""
    stop_event = MagicMock()
    stop_event.is_set.return_value = True # Stop right after login

    run_bot_instance(MagicMock(), stop_event, MagicMock())

    # Should not send any messages
    assert mock_dependencies['WhatsAppBot'].return_value.send_message.call_count == 0
