"""Diagnostic script to probe all known Blizzard endpoints during maintenance.

Run this when servers go down to see which endpoints are affected:
    python3 scripts/probe_endpoints.py
"""

import socket

ENDPOINTS = [
    ("us.actual.battle.net", 1119, "US login (what we check)"),
    ("eu.actual.battle.net", 1119, "EU login"),
    ("us.patch.battle.net", 1119, "US patch server"),
    ("us.version.battle.net", 1119, "US version server"),
    ("us.battle.net", 443, "Battle.net web (HTTPS)"),
]

TIMEOUT = 5

for host, port, label in ENDPOINTS:
    try:
        conn = socket.create_connection((host, port), timeout=TIMEOUT)
        conn.close()
        print(f"  UP    {label:40s} ({host}:{port})")
    except (socket.timeout, ConnectionRefusedError, OSError):
        print(f"  DOWN  {label:40s} ({host}:{port})")
