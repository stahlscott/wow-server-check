import argparse
import os
import sys
import time
from datetime import datetime

from wow_server_check.checker import (
    REGION_API_HOSTS,
    check_server,
    get_access_token,
)
from wow_server_check.notifier import notify

MINIMUM_INTERVAL = 10

GRADIENT_TIERS = [
    # (minutes_until_expected, interval_seconds)
    (60, 300),   # > 60 min away: check every 5 min
    (30, 120),   # 30–60 min away: check every 2 min
    (15, 60),    # 15–30 min away: check every 1 min
    (0, 30),     # < 15 min away: check every 30 sec
]


def get_gradient_interval(expected_up: datetime, now: datetime) -> int:
    minutes_remaining = (expected_up - now).total_seconds() / 60
    for threshold, interval in GRADIENT_TIERS:
        if minutes_remaining > threshold:
            return interval
    # Past expected time
    return GRADIENT_TIERS[-1][1]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check when WoW servers come back online after maintenance",
    )
    parser.add_argument(
        "--region",
        choices=list(REGION_API_HOSTS.keys()),
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
        "--expected-up",
        default=None,
        help="Expected up time in HH:MM format (local time). Enables gradient polling.",
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
    parser.add_argument(
        "--client-id",
        default=None,
        help="Blizzard API client ID (or set BLIZZARD_CLIENT_ID env var)",
    )
    parser.add_argument(
        "--client-secret",
        default=None,
        help="Blizzard API client secret (or set BLIZZARD_CLIENT_SECRET env var)",
    )

    args = parser.parse_args(argv)

    if args.interval < MINIMUM_INTERVAL:
        print(f"Warning: interval clamped to minimum of {MINIMUM_INTERVAL}s")
        args.interval = MINIMUM_INTERVAL

    if args.expected_up is not None:
        try:
            parsed_time = datetime.strptime(args.expected_up, "%H:%M").time()
            args.expected_up_dt = datetime.combine(datetime.today(), parsed_time)
        except ValueError:
            parser.error(f"Invalid time format '{args.expected_up}'. Use HH:MM (e.g., 14:00)")
    else:
        args.expected_up_dt = None

    return args


def _resolve_credentials(args: argparse.Namespace) -> tuple[str, str]:
    client_id = args.client_id or os.environ.get("BLIZZARD_CLIENT_ID", "")
    client_secret = args.client_secret or os.environ.get("BLIZZARD_CLIENT_SECRET", "")
    if not client_id or not client_secret:
        print(
            "Error: Blizzard API credentials required.\n"
            "Set BLIZZARD_CLIENT_ID and BLIZZARD_CLIENT_SECRET env vars,\n"
            "or pass --client-id and --client-secret flags.\n"
            "Get credentials at: https://develop.battle.net/access/clients",
            file=sys.stderr,
        )
        sys.exit(1)
    return client_id, client_secret


def _format_interval(seconds: int) -> str:
    if seconds >= 60:
        return f"{seconds // 60}m"
    return f"{seconds}s"


def main() -> None:
    args = parse_args()
    client_id, client_secret = _resolve_credentials(args)

    region_upper = args.region.upper()
    if args.expected_up_dt:
        print(
            f"Checking WoW servers ({region_upper}), "
            f"expected up at {args.expected_up} (gradient polling)...",
            flush=True,
        )
    else:
        print(f"Checking WoW servers ({region_upper}) every {args.interval}s...", flush=True)

    try:
        token = get_access_token(client_id, client_secret)
    except Exception as e:
        print(f"Error: Failed to authenticate with Blizzard API: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        while True:
            now = datetime.now()
            timestamp = now.strftime("%H:%M:%S")
            try:
                status = check_server(token=token, region=args.region)
            except Exception as e:
                print(f"[{timestamp}] Error checking servers: {e}", flush=True)
                time.sleep(args.interval)
                continue

            if status.all_up:
                print(f"[{timestamp}] Servers are UP! ({status.pct_up}%)", flush=True)
                notify(
                    "WoW servers are UP! Time to play!",
                    sound=args.sound,
                    desktop=args.notify,
                )
                return

            if args.expected_up_dt:
                interval = get_gradient_interval(args.expected_up_dt, now)
                print(
                    f"[{timestamp}] Servers are down... "
                    f"({status.pct_up}% up, next check in {_format_interval(interval)})",
                    flush=True,
                )
            else:
                interval = args.interval
                print(
                    f"[{timestamp}] Servers are down... ({status.pct_up}% up)",
                    flush=True,
                )

            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nStopped. Bye!")
