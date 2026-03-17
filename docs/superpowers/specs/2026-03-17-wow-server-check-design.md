# WoW Server Check — Design Spec

## Overview

A cross-platform CLI tool that polls the World of Warcraft login server during weekly maintenance and alerts the user when servers come back online. Designed to be shared with friends via GitHub — installable with a single `pipx` command, zero external dependencies.

## Problem

WoW servers go down every Tuesday for maintenance. The estimated "back up" time varies and servers often come up early or late. Players want to know the moment servers are available without manually refreshing or checking.

## Detection Method

TCP connection probe to the WoW login server.

- **Target:** `{region}.actual.battle.net` port `1119`
- **Regions:** `us` (default), `eu`, `kr`, `tw`
- **Method:** Open a TCP socket with a 5-second timeout
  - Connection accepted → servers are up
  - Timeout or connection refused → servers are down
- **Rationale:** The login server goes down during maintenance (verified 2026-03-17). A successful TCP connection is the most direct signal that the game is playable. This approach requires no API keys, no external dependencies, and responds in under 5 seconds.

## Notification

Two channels fire simultaneously when servers are detected as up:

### Sound

| Platform | Method |
|----------|--------|
| macOS | `afplay /System/Library/Sounds/{sound}.aiff` via subprocess |
| Linux | `paplay /usr/share/sounds/freedesktop/stereo/complete.oga`, fallback to terminal bell (`\a`) |
| Windows (future) | `winsound.PlaySound()` from stdlib |

Sound plays multiple times (3x with a short gap) to ensure it's noticed.

### Desktop Notification

| Platform | Method |
|----------|--------|
| macOS | `osascript -e 'display notification "..." with title "..."'` |
| Linux | `notify-send "WoW Server Check" "Servers are UP!"` |
| Windows (future) | `win10toast` or PowerShell fallback |

All methods use OS-native tools. No external Python dependencies.

If the current platform is unsupported, print a warning but don't crash — terminal output is the baseline notification.

## CLI Interface

```
wow-server-check [--region REGION] [--interval SECONDS] [--sound | --no-sound] [--notify | --no-notify]
```

| Flag | Default | Description |
|------|---------|-------------|
| `--region` | `us` | Server region: `us`, `eu`, `kr`, `tw` |
| `--interval` | `30` | Seconds between checks (minimum 10) |
| `--sound` / `--no-sound` | on | Toggle alert sound |
| `--notify` / `--no-notify` | on | Toggle desktop notification |

If `--interval` is set below 10, clamp to 10 and print a warning.

## Behavior

1. Print startup banner: `Checking WoW servers (US) every 30s...`
2. Poll loop: probe login server, print timestamped status each check
   - `[10:42:15] Servers are down...`
   - `[10:42:45] Servers are down...`
   - `[10:43:15] Servers are UP!`
3. On first successful connection: fire sound + desktop notification
4. Exit — the job is done

Ctrl+C exits cleanly with a brief message, no traceback.

## Project Structure

```
wow-server-check/
├── pyproject.toml
├── README.md
├── src/
│   └── wow_server_check/
│       ├── __init__.py
│       ├── cli.py          # Argument parsing, poll loop, entry point
│       ├── checker.py      # TCP connection probe
│       └── notifier.py     # Platform-dispatched sound + notification
```

### Module Responsibilities

- **`checker.py`** — Single function that probes the login server and returns a boolean. No side effects. Takes region and timeout as parameters.
- **`notifier.py`** — Platform detection via `platform.system()`. Exposes `notify(message, sound=True, desktop=True)` that dispatches to the right OS-native implementation.
- **`cli.py`** — `argparse`-based CLI, poll loop with `time.sleep()`, timestamped output, `KeyboardInterrupt` handling. Calls checker and notifier.

## Packaging

- `pyproject.toml` with `[project.scripts]` entry point: `wow-server-check = "wow_server_check.cli:main"`
- `src/` layout (modern Python packaging convention)
- Install: `pipx install git+https://github.com/{user}/wow-server-check`
- Also runnable via clone: `pip install -e .` then `wow-server-check`

## Dependencies

None. Stdlib only: `socket`, `subprocess`, `platform`, `argparse`, `time`, `datetime`.

## Platform Support

| Platform | Sound | Desktop Notification | Status |
|----------|-------|---------------------|--------|
| macOS | `afplay` | `osascript` | Shipping |
| Linux | `paplay` / bell | `notify-send` | Shipping |
| Windows | `winsound` | TBD | Future |

## Future Enhancements

- Windows notification support
- Slack / Discord webhook notification
- Battle.net API as secondary check
