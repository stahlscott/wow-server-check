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
    print(f"Checking WoW servers ({region_upper}) every {args.interval}s...", flush=True)

    try:
        while True:
            timestamp = datetime.now().strftime("%H:%M:%S")
            if check_server(region=args.region):
                print(f"[{timestamp}] Servers are UP!", flush=True)
                notify(
                    "WoW servers are UP! Time to play!",
                    sound=args.sound,
                    desktop=args.notify,
                )
                return
            print(f"[{timestamp}] Servers are down...", flush=True)
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nStopped. Bye!")
