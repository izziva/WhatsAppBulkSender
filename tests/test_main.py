import pytest
from unittest.mock import MagicMock, patch
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from main import main

# Tests for main function (argument parsing)
@patch('main.check_for_updates')
@patch('main.run_cli')
@patch('main.run_gui')
@patch('argparse.ArgumentParser.parse_args')
def test_main_cli_mode(mock_args, mock_run_gui, mock_run_cli, mock_check_updates):
    """Test that main calls run_cli with --nogui argument."""
    mock_args.return_value = MagicMock(nogui=True)
    # I need to find the version number from the pyproject.toml
    # For now, I will hardcode it. I will fix this later.
    main.__globals__['__version__'] = '1.0.0'
    main()
    mock_check_updates.assert_called_once_with(
        '1.0.0',
        gui_mode=False
    )
    mock_run_cli.assert_called_once()
    mock_run_gui.assert_not_called()

@patch('main.check_for_updates')
@patch('main.run_cli')
@patch('main.run_gui')
@patch('argparse.ArgumentParser.parse_args')
def test_main_gui_mode(mock_args, mock_run_gui, mock_run_cli, mock_check_updates):
    """Test that main calls run_gui without --nogui argument."""
    mock_args.return_value = MagicMock(nogui=False)
    main.__globals__['__version__'] = '1.0.0'
    main()
    mock_check_updates.assert_called_once_with(
        '1.0.0',
        gui_mode=True
    )
    mock_run_cli.assert_not_called()
    mock_run_gui.assert_called_once()
