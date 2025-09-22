import pytest
from unittest.mock import MagicMock, patch, mock_open
from whatsapp_sender.core.updater import get_platform_asset_name, check_for_updates

# Tests for get_platform_asset_name
@patch('platform.system')
def test_get_platform_asset_name_windows(mock_system):
    mock_system.return_value = "windows"
    assert get_platform_asset_name() == "whatsapp_sender-windows.exe"

@patch('platform.system')
def test_get_platform_asset_name_macos(mock_system):
    mock_system.return_value = "darwin"
    assert get_platform_asset_name() == "whatsapp_sender-macos.zip"

@patch('platform.system')
def test_get_platform_asset_name_linux(mock_system):
    mock_system.return_value = "linux"
    assert get_platform_asset_name() is None

# Tests for check_for_updates
@patch('whatsapp_sender.core.updater.httpx.Client')
def test_check_for_updates_new_version_yes(mock_client, mocker):
    """Test when a new version is available and user agrees to update."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"tag_name": "v1.1.0", "assets": []}
    mock_client.return_value.__enter__.return_value.get.return_value = mock_response

    mocker.patch('builtins.input', return_value='y')
    mock_download = mocker.patch('whatsapp_sender.core.updater.download_and_apply_update')

    check_for_updates("1.0.0")

    mock_download.assert_called_once()

@patch('whatsapp_sender.core.updater.httpx.Client')
def test_check_for_updates_new_version_no(mock_client, mocker):
    """Test when a new version is available and user declines."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"tag_name": "v1.1.0", "assets": []}
    mock_client.return_value.__enter__.return_value.get.return_value = mock_response

    mocker.patch('builtins.input', return_value='n')
    mock_download = mocker.patch('whatsapp_sender.core.updater.download_and_apply_update')

    check_for_updates("1.0.0")

    mock_download.assert_not_called()

@patch('whatsapp_sender.core.updater.httpx.Client')
def test_check_for_updates_latest_version(mock_client):
    """Test when the current version is the latest."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"tag_name": "v1.0.0"}
    mock_client.return_value.__enter__.return_value.get.return_value = mock_response

    check_for_updates("1.0.0")
    # No download should be triggered, just prints a message

@patch('whatsapp_sender.core.updater.httpx.Client')
def test_check_for_updates_request_error(mock_client):
    """Test when there is an error checking for updates."""
    mock_client.return_value.__enter__.return_value.get.side_effect = Exception("HTTP Error")

    # Should not raise an exception, just print an error
    check_for_updates("1.0.0")

# Tests for download_and_apply_update
@patch('whatsapp_sender.core.updater.get_platform_asset_name', return_value="whatsapp_sender-windows.exe")
@patch('whatsapp_sender.core.updater.httpx.stream')
@patch('builtins.open', new_callable=mock_open)
@patch('os.chmod')
@patch('whatsapp_sender.core.updater.apply_windows_update')
def test_download_and_apply_update_windows(mock_apply, mock_chmod, mock_open, mock_stream, mock_asset_name):
    release_info = {"assets": [{"name": "whatsapp_sender-windows.exe", "browser_download_url": "url", "size": 100}]}
    mock_stream.return_value.__enter__.return_value.iter_bytes.return_value = [b'chunk1', b'chunk2']

    from whatsapp_sender.core.updater import download_and_apply_update
    download_and_apply_update(release_info)

    mock_open.assert_called()
    mock_chmod.assert_called()
    mock_apply.assert_called_once()

@patch('whatsapp_sender.core.updater.get_platform_asset_name', return_value="unsupported.os")
def test_download_unsupported_os(mock_asset_name):
    from whatsapp_sender.core.updater import download_and_apply_update
    # Should not raise, just print error
    download_and_apply_update({"assets": []})

# Tests for apply_windows_update
@patch('builtins.open', new_callable=mock_open)
@patch('subprocess.Popen')
@patch('sys.exit')
def test_apply_windows_update(mock_exit, mock_popen, mock_open):
    from whatsapp_sender.core.updater import apply_windows_update
    apply_windows_update("temp/path.exe")

    mock_open.assert_called_once() # For the .bat file
    mock_popen.assert_called_once()
    mock_exit.assert_called_once_with(0)

# Tests for apply_macos_update
@patch('os.path.abspath', return_value="/path/to/app.app")
@patch('zipfile.ZipFile')
@patch('os.listdir', return_value=["new.app"])
@patch('shutil.rmtree')
@patch('shutil.move')
@patch('os.remove')
@patch('sys.exit')
def test_apply_macos_update(mock_exit, mock_remove, mock_move, mock_rmtree, mock_listdir, mock_zip, mock_abspath):
    from whatsapp_sender.core.updater import apply_macos_update
    apply_macos_update("temp/path.zip")

    mock_zip.assert_called_once()
    mock_rmtree.assert_called_once()
    mock_move.assert_called_once()
    mock_remove.assert_called_once()
    mock_exit.assert_called_once_with(0)

@patch('whatsapp_sender.core.updater.httpx.Client')
@patch('tkinter.messagebox.askyesno', return_value=True)
def test_check_for_updates_gui_mode_yes(mock_askyesno, mock_client, mocker):
    """Test GUI mode update check with a 'yes' answer."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"tag_name": "v1.1.0", "assets": []}
    mock_client.return_value.__enter__.return_value.get.return_value = mock_response

    mock_download = mocker.patch('whatsapp_sender.core.updater.download_and_apply_update')

    check_for_updates("1.0.0", gui_mode=True)

    mock_askyesno.assert_called_once()
    mock_download.assert_called_once()

@patch('whatsapp_sender.core.updater.httpx.Client')
@patch('tkinter.messagebox.askyesno', return_value=False)
def test_check_for_updates_gui_mode_no(mock_askyesno, mock_client, mocker):
    """Test GUI mode update check with a 'no' answer."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"tag_name": "v1.1.0", "assets": []}
    mock_client.return_value.__enter__.return_value.get.return_value = mock_response

    mock_download = mocker.patch('whatsapp_sender.core.updater.download_and_apply_update')

    check_for_updates("1.0.0", gui_mode=True)

    mock_askyesno.assert_called_once()
    mock_download.assert_not_called()

@patch('platform.system', return_value="darwin")
@patch('whatsapp_sender.core.updater.get_platform_asset_name', return_value="whatsapp_sender-macos.zip")
@patch('whatsapp_sender.core.updater.httpx.stream')
@patch('builtins.open', new_callable=mock_open)
@patch('whatsapp_sender.core.updater.apply_macos_update')
@patch('os.path.join', return_value="/tmp/temp_update.zip")
def test_download_and_apply_update_macos(mock_path_join, mock_apply_macos, mock_open, mock_stream, mock_asset_name, mock_system):
    """Test download and apply update for macOS."""
    release_info = {"assets": [{"name": "whatsapp_sender-macos.zip", "browser_download_url": "url", "size": 100}]}
    mock_stream.return_value.__enter__.return_value.iter_bytes.return_value = [b'chunk1']

    from whatsapp_sender.core.updater import download_and_apply_update
    download_and_apply_update(release_info)

    mock_apply_macos.assert_called_once()

@patch('os.path.abspath', return_value="/path/to/not-an-app")
def test_apply_macos_update_no_app_path(mock_abspath):
    """Test macOS update when the executable is not in a .app bundle."""
    from whatsapp_sender.core.updater import apply_macos_update
    apply_macos_update("temp/path.zip")
    # Should just print an error and return
