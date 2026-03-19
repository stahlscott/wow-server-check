# wow-server-check

A CLI tool that monitors World of Warcraft servers during weekly maintenance and alerts you the moment they come back online.

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

## Options

| Flag | Default | Description |
|------|---------|-------------|
| `--region` | `us` | Server region: `us`, `eu`, `kr`, `tw` |
| `--interval` | `30` | Seconds between checks (minimum: 10) |
| `--sound` / `--no-sound` | on | Toggle alert sound |
| `--notify` / `--no-notify` | on | Toggle desktop notification |

## How it works

Attempts a TCP connection to the WoW login server (`{region}.actual.battle.net:1119`). During maintenance, the server rejects connections. When it accepts one, the tool fires a sound alert and desktop notification, then exits.

## Platform support

| Platform | Sound | Desktop Notification |
|----------|-------|---------------------|
| macOS | Yes | Yes |
| Linux | Yes | Yes |
| Windows | Planned | Planned |

## Development

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

## License

MIT
