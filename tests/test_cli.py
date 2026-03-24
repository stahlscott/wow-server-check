from datetime import datetime
from unittest.mock import patch
from wow_server_check.checker import RealmStatus
from wow_server_check.cli import parse_args, get_gradient_interval, main


def test_parse_args_defaults():
    args = parse_args([])
    assert args.region == "us"
    assert args.interval == 30
    assert args.sound is True
    assert args.notify is True
    assert args.expected_up_dt is None


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


def test_parse_args_credentials():
    args = parse_args(["--client-id", "myid", "--client-secret", "mysecret"])
    assert args.client_id == "myid"
    assert args.client_secret == "mysecret"


def test_parse_args_expected_up():
    args = parse_args(["--expected-up", "14:00"])
    assert args.expected_up == "14:00"
    assert args.expected_up_dt is not None
    assert args.expected_up_dt.hour == 14
    assert args.expected_up_dt.minute == 0


def test_parse_args_expected_up_invalid():
    import pytest

    with pytest.raises(SystemExit):
        parse_args(["--expected-up", "not-a-time"])


# --- Gradient interval tests ---


def test_gradient_more_than_60_min_away():
    expected = datetime(2026, 3, 24, 14, 0)
    now = datetime(2026, 3, 24, 12, 0)  # 120 min away
    assert get_gradient_interval(expected, now) == 300  # 5 min


def test_gradient_30_to_60_min_away():
    expected = datetime(2026, 3, 24, 14, 0)
    now = datetime(2026, 3, 24, 13, 15)  # 45 min away
    assert get_gradient_interval(expected, now) == 120  # 2 min


def test_gradient_15_to_30_min_away():
    expected = datetime(2026, 3, 24, 14, 0)
    now = datetime(2026, 3, 24, 13, 40)  # 20 min away
    assert get_gradient_interval(expected, now) == 60  # 1 min


def test_gradient_less_than_15_min_away():
    expected = datetime(2026, 3, 24, 14, 0)
    now = datetime(2026, 3, 24, 13, 50)  # 10 min away
    assert get_gradient_interval(expected, now) == 30  # 30 sec


def test_gradient_past_expected_time():
    expected = datetime(2026, 3, 24, 14, 0)
    now = datetime(2026, 3, 24, 14, 30)  # 30 min past
    assert get_gradient_interval(expected, now) == 30  # 30 sec


# --- Main loop tests ---


@patch("wow_server_check.cli.get_access_token", return_value="fake-token")
@patch(
    "wow_server_check.cli.check_server",
    return_value=RealmStatus(total_up=83, total=83),
)
@patch("wow_server_check.cli.notify")
@patch.dict("os.environ", {"BLIZZARD_CLIENT_ID": "test-id", "BLIZZARD_CLIENT_SECRET": "test-secret"})
def test_main_exits_when_all_servers_up(mock_notify, mock_check, mock_auth):
    with patch("sys.argv", ["wow-server-check"]):
        main()
    mock_auth.assert_called_once_with("test-id", "test-secret")
    mock_check.assert_called_once()
    mock_notify.assert_called_once()


@patch("wow_server_check.cli.time.sleep")
@patch("wow_server_check.cli.get_access_token", return_value="fake-token")
@patch(
    "wow_server_check.cli.check_server",
    side_effect=[
        RealmStatus(total_up=10, total=83),
        RealmStatus(total_up=75, total=83),
        RealmStatus(total_up=83, total=83),
    ],
)
@patch("wow_server_check.cli.notify")
@patch.dict("os.environ", {"BLIZZARD_CLIENT_ID": "test-id", "BLIZZARD_CLIENT_SECRET": "test-secret"})
def test_main_polls_until_all_servers_up(mock_notify, mock_check, mock_auth, mock_sleep):
    with patch("sys.argv", ["wow-server-check"]):
        main()
    assert mock_check.call_count == 3
    assert mock_sleep.call_count == 2
    mock_notify.assert_called_once()


@patch("wow_server_check.cli.time.sleep")
@patch("wow_server_check.cli.get_access_token", return_value="fake-token")
@patch(
    "wow_server_check.cli.check_server",
    side_effect=[
        RealmStatus(total_up=10, total=83),
        KeyboardInterrupt,
    ],
)
@patch("wow_server_check.cli.notify")
@patch.dict("os.environ", {"BLIZZARD_CLIENT_ID": "test-id", "BLIZZARD_CLIENT_SECRET": "test-secret"})
def test_main_handles_keyboard_interrupt(mock_notify, mock_check, mock_auth, mock_sleep, capsys):
    with patch("sys.argv", ["wow-server-check"]):
        main()
    mock_notify.assert_not_called()
    captured = capsys.readouterr()
    assert "stopped" in captured.out.lower() or "bye" in captured.out.lower()


@patch.dict("os.environ", {}, clear=True)
def test_main_exits_without_credentials():
    import pytest

    with patch("sys.argv", ["wow-server-check"]):
        with pytest.raises(SystemExit):
            main()
