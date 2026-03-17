# WoW Server Check Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a cross-platform CLI tool that polls WoW login servers and alerts when maintenance ends.

**Architecture:** Three modules — `checker.py` (TCP probe), `notifier.py` (platform-dispatched alerts), `cli.py` (argument parsing + poll loop). Installed as a console script via `pyproject.toml`. Zero external runtime dependencies; `pytest` as dev dependency.

**Tech Stack:** Python 3.10+, stdlib only (`socket`, `subprocess`, `platform`, `argparse`, `time`, `datetime`), pytest for testing.

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `pyproject.toml` | Create | Package metadata, console script entry point, dev dependencies |
| `src/wow_server_check/__init__.py` | Create | Package init, version string |
| `src/wow_server_check/checker.py` | Create | TCP connection probe — single pure function |
| `src/wow_server_check/notifier.py` | Create | Platform-dispatched sound + desktop notification |
| `src/wow_server_check/cli.py` | Create | argparse CLI, poll loop, entry point |
| `tests/__init__.py` | Create | Test package init |
| `tests/test_checker.py` | Create | Tests for TCP probe logic |
| `tests/test_notifier.py` | Create | Tests for notification dispatch |
| `tests/test_cli.py` | Create | Tests for argument parsing and poll loop |
| `README.md` | Create | Install/usage instructions |

---

## Chunk 1: Project Scaffolding + Checker

### Task 1: Project scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `src/wow_server_check/__init__.py`
- Create: `tests/__init__.py`

- [ ] **Step 1: Create `pyproject.toml`**

```toml
[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.build_meta"

[project]
name = "wow-server-check"
version = "0.1.0"
description = "CLI tool that alerts you when WoW servers come back online after maintenance"
readme = "README.md"
requires-python = ">=3.10"
license = "MIT"

[project.scripts]
wow-server-check = "wow_server_check.cli:main"

[project.optional-dependencies]
dev = ["pytest>=7.0"]

[tool.setuptools.packages.find]
where = ["src"]
```

- [ ] **Step 2: Create `src/wow_server_check/__init__.py`**

```python
__version__ = "0.1.0"
```

- [ ] **Step 3: Create `tests/__init__.py`**

Empty file.

- [ ] **Step 4: Install the package in dev mode and verify pytest works**

Run: `cd /Users/scottstahl/code/wow-server-check && python3 -m pip install -e ".[dev]"`
Run: `cd /Users/scottstahl/code/wow-server-check && python3 -m pytest tests/ -v`
Expected: "no tests ran" (0 collected), exit 5 — confirms pytest finds the test directory.

- [ ] **Step 5: Commit**

```bash
git -C /Users/scottstahl/code/wow-server-check add pyproject.toml src/wow_server_check/__init__.py tests/__init__.py
git -C /Users/scottstahl/code/wow-server-check commit -m "chore: scaffold project with pyproject.toml and src layout"
```

---

### Task 2: Checker — TCP probe

**Files:**
- Create: `src/wow_server_check/checker.py`
- Create: `tests/test_checker.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_checker.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/scottstahl/code/wow-server-check && python3 -m pytest tests/test_checker.py -v`
Expected: ImportError — `checker` module doesn't exist yet.

- [ ] **Step 3: Implement `checker.py`**

Create `src/wow_server_check/checker.py`:

```python
import socket

REGION_HOSTS = {
    "us": "us.actual.battle.net",
    "eu": "eu.actual.battle.net",
    "kr": "kr.actual.battle.net",
    "tw": "tw.actual.battle.net",
}

PORT = 3724


def check_server(region: str = "us", timeout: int = 5) -> bool:
    host = REGION_HOSTS[region]
    try:
        conn = socket.create_connection((host, PORT), timeout=timeout)
        conn.close()
        return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/scottstahl/code/wow-server-check && python3 -m pytest tests/test_checker.py -v`
Expected: All 7 tests PASS.

- [ ] **Step 5: Commit**

```bash
git -C /Users/scottstahl/code/wow-server-check add src/wow_server_check/checker.py tests/test_checker.py
git -C /Users/scottstahl/code/wow-server-check commit -m "feat: add TCP server checker with region support"
```

---

## Chunk 2: Notifier

### Task 3: Notifier — platform-dispatched alerts

**Files:**
- Create: `src/wow_server_check/notifier.py`
- Create: `tests/test_notifier.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_notifier.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/scottstahl/code/wow-server-check && python3 -m pytest tests/test_notifier.py -v`
Expected: ImportError — `notifier` module doesn't exist yet.

- [ ] **Step 3: Implement `notifier.py`**

Create `src/wow_server_check/notifier.py`:

```python
import platform
import subprocess
import time


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
    subprocess.run(
        ["osascript", "-e", f'display notification "{message}" with title "WoW Server Check"'],
        check=False,
    )


def _notify_desktop_linux(message: str) -> None:
    subprocess.run(
        ["notify-send", "WoW Server Check", message],
        check=False,
    )


def notify(message: str, sound: bool = True, desktop: bool = True) -> None:
    system = platform.system()

    if sound:
        if system == "Darwin":
            _play_sound_macos()
        elif system == "Linux":
            _play_sound_linux()
        else:
            print("\a", end="", flush=True)

    if desktop:
        if system == "Darwin":
            _notify_desktop_macos(message)
        elif system == "Linux":
            _notify_desktop_linux(message)
        else:
            print(f"[WoW Server Check] {message} (desktop notifications unsupported on {system})")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/scottstahl/code/wow-server-check && python3 -m pytest tests/test_notifier.py -v`
Expected: All 9 tests PASS.

- [ ] **Step 5: Commit**

```bash
git -C /Users/scottstahl/code/wow-server-check add src/wow_server_check/notifier.py tests/test_notifier.py
git -C /Users/scottstahl/code/wow-server-check commit -m "feat: add platform-dispatched notifications (macOS + Linux)"
```

---

## Chunk 3: CLI + Integration

### Task 4: CLI — argument parsing and poll loop

**Files:**
- Create: `src/wow_server_check/cli.py`
- Create: `tests/test_cli.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_cli.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/scottstahl/code/wow-server-check && python3 -m pytest tests/test_cli.py -v`
Expected: ImportError — `cli` module doesn't exist yet.

- [ ] **Step 3: Implement `cli.py`**

Create `src/wow_server_check/cli.py`:

```python
import argparse
import sys
import time
from datetime import datetime

from wow_server_check.checker import check_server, REGION_HOSTS
from wow_server_check.notifier import notify

MINIMUM_INTERVAL = 10


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check when WoW servers come back online after maintenance",
    )
    parser.add_argument(
        "--region",
        choices=list(REGION_HOSTS.keys()),
        default="us",
        help="Server region (default: us)",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=30,
        help=f"Seconds between checks (default: 30, minimum: {MINIMUM_INTERVAL})",
    )
    parser.add_argument(
        "--sound",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Play alert sound (default: on)",
    )
    parser.add_argument(
        "--notify",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Show desktop notification (default: on)",
    )

    args = parser.parse_args(argv)

    if args.interval < MINIMUM_INTERVAL:
        print(f"Warning: interval clamped to minimum of {MINIMUM_INTERVAL}s")
        args.interval = MINIMUM_INTERVAL

    return args


def main() -> None:
    args = parse_args()
    region_upper = args.region.upper()
    print(f"Checking WoW servers ({region_upper}) every {args.interval}s...")

    try:
        while True:
            timestamp = datetime.now().strftime("%H:%M:%S")
            if check_server(region=args.region):
                print(f"[{timestamp}] Servers are UP!")
                notify(
                    "WoW servers are UP! Time to play!",
                    sound=args.sound,
                    desktop=args.notify,
                )
                return
            print(f"[{timestamp}] Servers are down...")
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nStopped. Bye!")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/scottstahl/code/wow-server-check && python3 -m pytest tests/test_cli.py -v`
Expected: All 9 tests PASS.

- [ ] **Step 5: Run full test suite**

Run: `cd /Users/scottstahl/code/wow-server-check && python3 -m pytest tests/ -v`
Expected: All 25 tests PASS.

- [ ] **Step 6: Verify CLI entry point works**

Run: `cd /Users/scottstahl/code/wow-server-check && wow-server-check --help`
Expected: Help text showing all flags and their defaults.

- [ ] **Step 7: Commit**

```bash
git -C /Users/scottstahl/code/wow-server-check add src/wow_server_check/cli.py tests/test_cli.py
git -C /Users/scottstahl/code/wow-server-check commit -m "feat: add CLI with poll loop and argument parsing"
```

---

### Task 5: README

**Files:**
- Create: `README.md`

- [ ] **Step 1: Write README**

Create `README.md`:

````markdown
# wow-server-check

A CLI tool that monitors World of Warcraft servers during weekly maintenance and alerts you the moment they come back online.

## Install

```bash
pipx install git+https://github.com/YOUR_USERNAME/wow-server-check
```

Or clone and install locally:

```bash
git clone https://github.com/YOUR_USERNAME/wow-server-check
cd wow-server-check
pip install .
```

## Usage

```bash
# Default: check US servers every 30 seconds
wow-server-check

# Check EU servers every 60 seconds
wow-server-check --region eu --interval 60

# Disable sound, only show desktop notification
wow-server-check --no-sound
```

## Options

| Flag | Default | Description |
|------|---------|-------------|
| `--region` | `us` | Server region: `us`, `eu`, `kr`, `tw` |
| `--interval` | `30` | Seconds between checks (minimum: 10) |
| `--sound` / `--no-sound` | on | Toggle alert sound |
| `--notify` / `--no-notify` | on | Toggle desktop notification |

## How it works

Attempts a TCP connection to the WoW login server (`{region}.actual.battle.net:3724`). During maintenance, the server rejects connections. When it accepts one, the tool fires a sound alert and desktop notification, then exits.

## Platform support

| Platform | Sound | Desktop Notification |
|----------|-------|---------------------|
| macOS | ✅ | ✅ |
| Linux | ✅ | ✅ |
| Windows | Planned | Planned |

## Development

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

## License

MIT
````

- [ ] **Step 2: Commit**

```bash
git -C /Users/scottstahl/code/wow-server-check add README.md
git -C /Users/scottstahl/code/wow-server-check commit -m "docs: add README with install and usage instructions"
```

---

### Task 6: Manual smoke test

- [ ] **Step 1: Run the tool against live servers**

Run: `cd /Users/scottstahl/code/wow-server-check && wow-server-check --interval 10`

If servers are currently down (maintenance Tuesday): verify it prints "Servers are down..." every 10 seconds. Ctrl+C to stop. Verify clean exit message.

If servers are currently up: verify it prints "Servers are UP!", plays the sound, shows the notification, and exits.

- [ ] **Step 2: Verify notification works**

Run a quick one-off test of the notification:

```bash
cd /Users/scottstahl/code/wow-server-check && python3 -c "from wow_server_check.notifier import notify; notify('Test alert!')"
```

Verify: sound plays 3 times, macOS notification appears.
