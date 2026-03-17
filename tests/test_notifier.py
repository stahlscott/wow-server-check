from unittest.mock import patch, call
from wow_server_check.notifier import notify, _play_sound_macos, _play_sound_linux, _notify_desktop_macos, _notify_desktop_linux


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
