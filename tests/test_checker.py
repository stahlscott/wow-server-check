from unittest.mock import patch, MagicMock
from wow_server_check.checker import check_server, REGION_HOSTS


def test_region_hosts_contains_us():
    assert "us" in REGION_HOSTS
    assert REGION_HOSTS["us"] == "us.actual.battle.net"


def test_region_hosts_contains_all_regions():
    for region in ("us", "eu", "kr", "tw"):
        assert region in REGION_HOSTS


def test_check_server_returns_true_when_connection_succeeds():
    with patch("wow_server_check.checker.socket.create_connection") as mock_conn:
        mock_sock = MagicMock()
        mock_conn.return_value = mock_sock
        assert check_server(region="us", timeout=5) is True
        mock_conn.assert_called_once_with(("us.actual.battle.net", 3724), timeout=5)
        mock_sock.close.assert_called_once()


def test_check_server_returns_false_on_timeout():
    with patch("wow_server_check.checker.socket.create_connection") as mock_conn:
        import socket
        mock_conn.side_effect = socket.timeout("timed out")
        assert check_server(region="us", timeout=5) is False


def test_check_server_returns_false_on_connection_refused():
    with patch("wow_server_check.checker.socket.create_connection") as mock_conn:
        mock_conn.side_effect = ConnectionRefusedError("refused")
        assert check_server(region="us", timeout=5) is False


def test_check_server_returns_false_on_os_error():
    with patch("wow_server_check.checker.socket.create_connection") as mock_conn:
        mock_conn.side_effect = OSError("network unreachable")
        assert check_server(region="us", timeout=5) is False


def test_check_server_defaults_to_us_region():
    with patch("wow_server_check.checker.socket.create_connection") as mock_conn:
        mock_sock = MagicMock()
        mock_conn.return_value = mock_sock
        check_server()
        mock_conn.assert_called_once_with(("us.actual.battle.net", 3724), timeout=5)
