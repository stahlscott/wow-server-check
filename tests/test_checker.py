import json
from unittest.mock import patch, MagicMock
from wow_server_check.checker import (
    check_server,
    get_access_token,
    RealmStatus,
    REGION_API_HOSTS,
)


def test_region_api_hosts_contains_us():
    assert "us" in REGION_API_HOSTS
    assert REGION_API_HOSTS["us"] == "us.api.blizzard.com"


def test_region_api_hosts_contains_all_regions():
    for region in ("us", "eu", "kr", "tw"):
        assert region in REGION_API_HOSTS


def test_realm_status_pct_up():
    status = RealmStatus(total_up=75, total=83)
    assert status.pct_up == 90


def test_realm_status_pct_up_zero_total():
    status = RealmStatus(total_up=0, total=0)
    assert status.pct_up == 0


def test_realm_status_all_up():
    status = RealmStatus(total_up=83, total=83)
    assert status.all_up is True


def test_realm_status_not_all_up():
    status = RealmStatus(total_up=80, total=83)
    assert status.all_up is False


def _mock_urlopen(responses):
    """Helper that returns a mock urlopen which serves responses in order."""
    call_count = [0]

    def side_effect(req, timeout=None):
        resp = MagicMock()
        resp.read.return_value = json.dumps(responses[call_count[0]]).encode()
        call_count[0] += 1
        return resp

    return side_effect


def test_get_access_token():
    token_response = {"access_token": "test-token-123", "expires_in": 86399}
    with patch("wow_server_check.checker.urllib.request.urlopen") as mock_urlopen:
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(token_response).encode()
        mock_urlopen.return_value = mock_resp
        token = get_access_token("my-id", "my-secret")
        assert token == "test-token-123"


def test_check_server_all_up():
    all_realms_resp = {
        "pageCount": 1,
        "results": [
            {"data": {"status": {"type": "UP"}}},
            {"data": {"status": {"type": "UP"}}},
        ],
    }

    with patch("wow_server_check.checker.urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.side_effect = _mock_urlopen([all_realms_resp])
        status = check_server(token="fake-token", region="us")
        assert status.total_up == 2
        assert status.total == 2
        assert status.all_up is True


def test_check_server_some_down():
    all_realms_resp = {
        "pageCount": 1,
        "results": [
            {"data": {"status": {"type": "UP"}}},
            {"data": {"status": {"type": "DOWN"}}},
            {"data": {"status": {"type": "DOWN"}}},
        ],
    }

    with patch("wow_server_check.checker.urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.side_effect = _mock_urlopen([all_realms_resp])
        status = check_server(token="fake-token", region="us")
        assert status.total_up == 1
        assert status.total == 3
        assert status.all_up is False


def test_check_server_invalid_region():
    import pytest

    with pytest.raises(ValueError, match="Unknown region"):
        check_server(token="fake-token", region="cn")


def test_check_server_multiple_pages():
    page1_resp = {
        "pageCount": 2,
        "results": [{"data": {"status": {"type": "UP"}}}],
    }
    page2_resp = {
        "pageCount": 2,
        "results": [{"data": {"status": {"type": "DOWN"}}}],
    }

    with patch("wow_server_check.checker.urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.side_effect = _mock_urlopen([page1_resp, page2_resp])
        status = check_server(token="fake-token", region="us")
        assert status.total_up == 1
        assert status.total == 2
        assert status.all_up is False
