from unittest.mock import patch, MagicMock
from wow_server_check.cli import parse_args, main


def test_parse_args_defaults():
    args = parse_args([])
    assert args.region == "us"
    assert args.interval == 30
    assert args.sound is True
    assert args.notify is True


def test_parse_args_custom_region():
    args = parse_args(["--region", "eu"])
    assert args.region == "eu"


def test_parse_args_custom_interval():
    args = parse_args(["--interval", "60"])
    assert args.interval == 60


def test_parse_args_interval_clamped_to_minimum():
    args = parse_args(["--interval", "5"])
    assert args.interval == 10


def test_parse_args_no_sound():
    args = parse_args(["--no-sound"])
    assert args.sound is False


def test_parse_args_no_notify():
    args = parse_args(["--no-notify"])
    assert args.notify is False


@patch("wow_server_check.cli.check_server", return_value=True)
@patch("wow_server_check.cli.notify")
def test_main_exits_when_server_is_up(mock_notify, mock_check):
    with patch("sys.argv", ["wow-server-check"]):
        main()
    mock_check.assert_called_once()
    mock_notify.assert_called_once()


@patch("wow_server_check.cli.time.sleep")
@patch("wow_server_check.cli.check_server", side_effect=[False, False, True])
@patch("wow_server_check.cli.notify")
def test_main_polls_until_server_is_up(mock_notify, mock_check, mock_sleep):
    with patch("sys.argv", ["wow-server-check"]):
        main()
    assert mock_check.call_count == 3
    assert mock_sleep.call_count == 2  # sleeps between checks, not after success
    mock_notify.assert_called_once()


@patch("wow_server_check.cli.time.sleep")
@patch("wow_server_check.cli.notify")
@patch("wow_server_check.cli.check_server", side_effect=[False, KeyboardInterrupt])
def test_main_handles_keyboard_interrupt(mock_check, mock_notify, mock_sleep, capsys):
    with patch("sys.argv", ["wow-server-check"]):
        main()
    mock_notify.assert_not_called()
    captured = capsys.readouterr()
    assert "stopped" in captured.out.lower() or "bye" in captured.out.lower() or "exit" in captured.out.lower()
