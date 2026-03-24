# wow-server-check

A CLI tool that monitors World of Warcraft servers during weekly maintenance and alerts you the moment they come back online.

Uses the official Blizzard Game Data API to check realm status, so you know when maintenance is truly over (not just a brief flicker).

## Prerequisites

You need a free Blizzard API key:

1. Go to https://develop.battle.net/access/clients
2. Log in with your Battle.net account
3. Create a client (any name, redirect URL: `https://localhost`)
4. Set environment variables:

```bash
export BLIZZARD_CLIENT_ID=your_client_id
export BLIZZARD_CLIENT_SECRET=your_client_secret
```

Or pass them as flags: `--client-id` and `--client-secret`.

## Install

```bash
pipx install git+https://github.com/stahlscott/wow-server-check
```

Or clone and install locally:

```bash
git clone https://github.com/stahlscott/wow-server-check
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

Example output during maintenance:
```
Checking WoW servers (US) every 30s...
[10:42:15] Servers are down... (12% up)
[10:42:45] Servers are down... (67% up)
[10:43:15] Servers are down... (98% up)
[10:43:45] Servers are UP! (100%)
```

## Options

| Flag | Default | Description |
|------|---------|-------------|
| `--region` | `us` | Server region: `us`, `eu`, `kr`, `tw` |
| `--interval` | `30` | Seconds between checks (minimum: 10) |
| `--sound` / `--no-sound` | on | Toggle alert sound |
| `--notify` / `--no-notify` | on | Toggle desktop notification |
| `--client-id` | env var | Blizzard API client ID |
| `--client-secret` | env var | Blizzard API client secret |

## How it works

Queries the Blizzard Game Data API for connected realm status across the region. Declares maintenance over only when **all realms are UP** — this avoids false positives from realms flickering up during rolling restarts.

## Platform support

| Platform | Sound | Desktop Notification |
|----------|-------|---------------------|
| macOS | Yes | Yes |
| Linux | Yes | Yes |
| Windows | Planned | Planned |

## Development

```bash
cp .env.example .env  # add your Blizzard API credentials
pip install -e ".[dev]"
pytest tests/ -v
```

## License

MIT
