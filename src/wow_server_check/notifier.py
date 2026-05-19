import json
import os
import platform
import subprocess
import time
import urllib.request


def _play_sound_macos() -> None:
    sound_path = "/System/Library/Sounds/Glass.aiff"
    for _ in range(3):
        subprocess.run(["afplay", sound_path], check=False)
        time.sleep(0.5)


def _play_sound_linux() -> None:
    sound_path = "/usr/share/sounds/freedesktop/stereo/complete.oga"
    for _ in range(3):
        try:
            subprocess.run(["paplay", sound_path], check=True)
        except (FileNotFoundError, subprocess.CalledProcessError):
            print("\a", end="", flush=True)
        time.sleep(0.5)


def _notify_desktop_macos(message: str) -> None:
    escaped = message.replace("\\", "\\\\").replace('"', '\\"')
    subprocess.run(
        ["osascript", "-e", f'display notification "{escaped}" with title "WoW Server Check"'],
        check=False,
    )


def _notify_desktop_linux(message: str) -> None:
    subprocess.run(
        ["notify-send", "WoW Server Check", message],
        check=False,
    )


def _notify_discord(message: str, webhook_url: str, role_id: str | None = None) -> None:
    content = f"<@&{role_id}> {message}" if role_id else message
    payload = json.dumps({"content": content}).encode()
    req = urllib.request.Request(
        webhook_url,
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        urllib.request.urlopen(req, timeout=10)
    except Exception:
        pass


def notify(message: str, sound: bool = True, desktop: bool = True, discord: bool = True) -> None:
    system = platform.system()

    if desktop:
        if system == "Darwin":
            _notify_desktop_macos(message)
        elif system == "Linux":
            _notify_desktop_linux(message)
        else:
            print(f"[WoW Server Check] {message} (desktop notifications unsupported on {system})")

    if sound:
        if system == "Darwin":
            _play_sound_macos()
        elif system == "Linux":
            _play_sound_linux()
        else:
            print("\a", end="", flush=True)

    if discord:
        webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
        if webhook_url:
            role_id = os.environ.get("DISCORD_ROLE_ID") or None
            _notify_discord(message, webhook_url, role_id=role_id)
