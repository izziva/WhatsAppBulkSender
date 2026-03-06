import pytest
from unittest.mock import MagicMock, patch
from whatsapp_sender.utils.driver_utils import create_driver

@patch('whatsapp_sender.utils.driver_utils.webdriver.Chrome')
@patch('whatsapp_sender.utils.driver_utils.ChromeDriverManager')
@patch('whatsapp_sender.utils.driver_utils.Options')
def test_create_driver_success(mock_options, mock_cdm, mock_chrome):
    """Test the successful creation of the Chrome driver."""
    mock_options_instance = MagicMock()
    mock_options.return_value = mock_options_instance

    mock_cdm_instance = MagicMock()
    mock_cdm_instance.install.return_value = "path/to/driver"
    mock_cdm.return_value = mock_cdm_instance

    driver = create_driver()

    assert mock_options.called
    assert mock_options_instance.add_argument.call_count > 5 # Check that arguments are being added
    mock_cdm.return_value.install.assert_called_once()
    mock_chrome.assert_called_once()
    assert driver == mock_chrome.return_value

@patch('whatsapp_sender.utils.driver_utils.webdriver.Chrome', side_effect=Exception("Test Error"))
@patch('whatsapp_sender.utils.driver_utils.ChromeDriverManager')
@patch('whatsapp_sender.utils.driver_utils.Options')
def test_create_driver_exception(mock_options, mock_cdm, mock_chrome):
    """Test that an exception during driver creation is raised."""
    with pytest.raises(Exception, match="Test Error"):
        create_driver()
