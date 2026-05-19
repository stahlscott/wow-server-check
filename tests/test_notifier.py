import json
from unittest.mock import patch, call, MagicMock
from wow_server_check.notifier import notify, _play_sound_macos, _play_sound_linux, _notify_desktop_macos, _notify_desktop_linux, _notify_discord


@patch("wow_server_check.notifier.time.sleep")
@patch("wow_server_check.notifier.subprocess.run")
def test_play_sound_macos_calls_afplay(mock_run, mock_sleep):
    _play_sound_macos()
    assert mock_run.call_count == 3  # plays 3 times


@patch("wow_server_check.notifier.time.sleep")
@patch("wow_server_check.notifier.subprocess.run")
def test_play_sound_linux_tries_paplay(mock_run, mock_sleep):
    _play_sound_linux()
    assert mock_run.call_count == 3


@patch("wow_server_check.notifier.subprocess.run")
def test_notify_desktop_macos_calls_osascript(mock_run):
    _notify_desktop_macos("Servers are UP!")
    mock_run.assert_called_once()
    cmd = mock_run.call_args[0][0]
    assert "osascript" in cmd


@patch("wow_server_check.notifier.subprocess.run")
def test_notify_desktop_linux_calls_notify_send(mock_run):
    _notify_desktop_linux("Servers are UP!")
    mock_run.assert_called_once()
    cmd = mock_run.call_args[0][0]
    assert "notify-send" in cmd


@patch("wow_server_check.notifier.platform.system", return_value="Darwin")
@patch("wow_server_check.notifier._play_sound_macos")
@patch("wow_server_check.notifier._notify_desktop_macos")
def test_notify_dispatches_to_macos(mock_desktop, mock_sound, mock_platform):
    notify("Servers are UP!")
    mock_sound.assert_called_once()
    mock_desktop.assert_called_once_with("Servers are UP!")


@patch("wow_server_check.notifier.platform.system", return_value="Linux")
@patch("wow_server_check.notifier._play_sound_linux")
@patch("wow_server_check.notifier._notify_desktop_linux")
def test_notify_dispatches_to_linux(mock_desktop, mock_sound, mock_platform):
    notify("Servers are UP!")
    mock_sound.assert_called_once()
    mock_desktop.assert_called_once_with("Servers are UP!")


@patch("wow_server_check.notifier.platform.system", return_value="Darwin")
@patch("wow_server_check.notifier._play_sound_macos")
@patch("wow_server_check.notifier._notify_desktop_macos")
def test_notify_respects_sound_false(mock_desktop, mock_sound, mock_platform):
    notify("Servers are UP!", sound=False)
    mock_sound.assert_not_called()
    mock_desktop.assert_called_once()


@patch("wow_server_check.notifier.platform.system", return_value="Darwin")
@patch("wow_server_check.notifier._play_sound_macos")
@patch("wow_server_check.notifier._notify_desktop_macos")
def test_notify_respects_desktop_false(mock_desktop, mock_sound, mock_platform):
    notify("Servers are UP!", desktop=False)
    mock_sound.assert_called_once()
    mock_desktop.assert_not_called()


@patch("wow_server_check.notifier.platform.system", return_value="Windows")
@patch("builtins.print")
def test_notify_unsupported_platform_prints_warning(mock_print, mock_platform):
    notify("Servers are UP!")
    # Should not crash, just print
    assert any("unsupported" in str(c).lower() or "UP" in str(c) for c in mock_print.call_args_list)


# --- Discord notification tests ---


class TestNotifyDiscord:
    def test_posts_json_to_webhook_url(self):
        mock_urlopen = MagicMock()
        with patch("wow_server_check.notifier.urllib.request.urlopen", mock_urlopen):
            _notify_discord("Servers are UP!", "https://discord.com/api/webhooks/123/abc")

        mock_urlopen.assert_called_once()
        req = mock_urlopen.call_args[0][0]
        assert req.full_url == "https://discord.com/api/webhooks/123/abc"
        assert req.get_header("Content-type") == "application/json"
        body = json.loads(req.data)
        assert body["content"] == "Servers are UP!"

    def test_includes_role_mention_when_role_id_provided(self):
        mock_urlopen = MagicMock()
        with patch("wow_server_check.notifier.urllib.request.urlopen", mock_urlopen):
            _notify_discord("Servers are UP!", "https://discord.com/api/webhooks/123/abc", role_id="999")

        body = json.loads(mock_urlopen.call_args[0][0].data)
        assert "<@&999>" in body["content"]
        assert "Servers are UP!" in body["content"]

    def test_no_role_mention_when_role_id_absent(self):
        mock_urlopen = MagicMock()
        with patch("wow_server_check.notifier.urllib.request.urlopen", mock_urlopen):
            _notify_discord("Servers are UP!", "https://discord.com/api/webhooks/123/abc")

        body = json.loads(mock_urlopen.call_args[0][0].data)
        assert "<@&" not in body["content"]

    def test_silently_handles_http_error(self):
        with patch(
            "wow_server_check.notifier.urllib.request.urlopen",
            side_effect=Exception("Connection refused"),
        ):
            _notify_discord("msg", "https://discord.com/api/webhooks/123/abc")


class TestNotifyDiscordIntegration:
    @patch("wow_server_check.notifier._notify_discord")
    @patch("wow_server_check.notifier._play_sound_macos")
    @patch("wow_server_check.notifier._notify_desktop_macos")
    @patch("wow_server_check.notifier.platform.system", return_value="Darwin")
    def test_calls_discord_when_webhook_url_set(self, _sys, _desk, _snd, mock_discord):
        with patch.dict("os.environ", {"DISCORD_WEBHOOK_URL": "https://discord.com/api/webhooks/123/abc"}):
            notify("test message", discord=True)
        mock_discord.assert_called_once_with("test message", "https://discord.com/api/webhooks/123/abc", role_id=None)

    @patch("wow_server_check.notifier._notify_discord")
    @patch("wow_server_check.notifier._play_sound_macos")
    @patch("wow_server_check.notifier._notify_desktop_macos")
    @patch("wow_server_check.notifier.platform.system", return_value="Darwin")
    def test_passes_role_id_when_set(self, _sys, _desk, _snd, mock_discord):
        with patch.dict("os.environ", {"DISCORD_WEBHOOK_URL": "https://hook", "DISCORD_ROLE_ID": "42"}):
            notify("test message", discord=True)
        mock_discord.assert_called_once_with("test message", "https://hook", role_id="42")

    @patch("wow_server_check.notifier._notify_discord")
    @patch("wow_server_check.notifier._play_sound_macos")
    @patch("wow_server_check.notifier._notify_desktop_macos")
    @patch("wow_server_check.notifier.platform.system", return_value="Darwin")
    def test_skips_discord_when_no_webhook_url(self, _sys, _desk, _snd, mock_discord):
        with patch.dict("os.environ", {}, clear=True):
            notify("test message", discord=True)
        mock_discord.assert_not_called()

    @patch("wow_server_check.notifier._notify_discord")
    @patch("wow_server_check.notifier._play_sound_macos")
    @patch("wow_server_check.notifier._notify_desktop_macos")
    @patch("wow_server_check.notifier.platform.system", return_value="Darwin")
    def test_skips_discord_when_flag_is_false(self, _sys, _desk, _snd, mock_discord):
        with patch.dict("os.environ", {"DISCORD_WEBHOOK_URL": "https://hook"}):
            notify("test message", discord=False)
        mock_discord.assert_not_called()
