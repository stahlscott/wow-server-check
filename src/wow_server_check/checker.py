import socket

REGION_HOSTS = {
    "us": "us.actual.battle.net",
    "eu": "eu.actual.battle.net",
    "kr": "kr.actual.battle.net",
    "tw": "tw.actual.battle.net",
}

PORT = 1119


def check_server(region: str = "us", timeout: int = 5) -> bool:
    host = REGION_HOSTS[region]
    try:
        conn = socket.create_connection((host, PORT), timeout=timeout)
        conn.close()
        return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False
