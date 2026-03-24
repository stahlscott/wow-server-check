import argparse
import os
import sys
import time
from datetime import datetime

from wow_server_check.checker import (
    REGION_API_HOSTS,
    DEFAULT_REALM,
    check_server,
    get_access_token,
)
from wow_server_check.notifier import notify

MINIMUM_INTERVAL = 10


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
        "--realm",
        default=DEFAULT_REALM,
        help=f"Realm name to check (default: {DEFAULT_REALM})",
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


def main() -> None:
    args = parse_args()
    client_id, client_secret = _resolve_credentials(args)

    region_upper = args.region.upper()
    print(
        f"Checking WoW servers ({region_upper}, realm: {args.realm}) every {args.interval}s...",
        flush=True,
    )

    try:
        token = get_access_token(client_id, client_secret)
    except Exception as e:
        print(f"Error: Failed to authenticate with Blizzard API: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        while True:
            timestamp = datetime.now().strftime("%H:%M:%S")
            try:
                status = check_server(token=token, region=args.region, realm=args.realm)
            except Exception as e:
                print(f"[{timestamp}] Error checking servers: {e}", flush=True)
                time.sleep(args.interval)
                continue

            if status.all_up:
                print(
                    f"[{timestamp}] Servers are UP! "
                    f"({status.pct_up}% — {args.realm}: UP)",
                    flush=True,
                )
                notify(
                    "WoW servers are UP! Time to play!",
                    sound=args.sound,
                    desktop=args.notify,
                )
                return

            realm_label = "UP" if status.realm_up else "DOWN"
            if status.realm_up:
                print(
                    f"[{timestamp}] Almost there... "
                    f"({status.pct_up}% up — {args.realm}: UP, waiting for all realms)",
                    flush=True,
                )
            else:
                print(
                    f"[{timestamp}] Servers are down... "
                    f"({status.pct_up}% up — {args.realm}: {realm_label})",
                    flush=True,
                )
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nStopped. Bye!")
