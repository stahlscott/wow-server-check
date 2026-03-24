import json
import urllib.parse
import urllib.request
from base64 import b64encode
from dataclasses import dataclass

REGION_API_HOSTS = {
    "us": "us.api.blizzard.com",
    "eu": "eu.api.blizzard.com",
    "kr": "kr.api.blizzard.com",
    "tw": "tw.api.blizzard.com",
}

TOKEN_URL = "https://oauth.battle.net/token"

DEFAULT_REALM = "Sargeras"


@dataclass
class RealmStatus:
    realm_name: str
    realm_up: bool
    total_up: int
    total: int

    @property
    def pct_up(self) -> int:
        if self.total == 0:
            return 0
        return round(100 * self.total_up / self.total)

    @property
    def all_up(self) -> bool:
        return self.total > 0 and self.total_up == self.total


def get_access_token(client_id: str, client_secret: str) -> str:
    credentials = b64encode(f"{client_id}:{client_secret}".encode()).decode()
    data = urllib.parse.urlencode({"grant_type": "client_credentials"}).encode()
    req = urllib.request.Request(
        TOKEN_URL,
        data=data,
        headers={"Authorization": f"Basic {credentials}"},
    )
    resp = json.loads(urllib.request.urlopen(req, timeout=10).read())
    return resp["access_token"]


def _api_get(url: str, token: str) -> dict:
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    return json.loads(urllib.request.urlopen(req, timeout=10).read())


def check_server(
    token: str,
    region: str = "us",
    realm: str = DEFAULT_REALM,
) -> RealmStatus:
    api_host = REGION_API_HOSTS.get(region)
    if api_host is None:
        raise ValueError(f"Unknown region {region!r}. Valid regions: {list(REGION_API_HOSTS)}")

    namespace = f"dynamic-{region}"

    # Check the user's specific realm first
    search_url = (
        f"https://{api_host}/data/wow/search/connected-realm"
        f"?namespace={namespace}"
        f"&realms.name.en_US={urllib.parse.quote(realm)}"
    )
    search_resp = _api_get(search_url, token)
    results = search_resp.get("results", [])

    realm_up = False
    if results:
        status = results[0].get("data", {}).get("status", {}).get("type", "DOWN")
        realm_up = status == "UP"

    # Count total UP vs DOWN across all connected realms
    total_up = 0
    total = 0
    page = 1
    while True:
        index_url = (
            f"https://{api_host}/data/wow/search/connected-realm"
            f"?namespace={namespace}&orderby=id&_page={page}"
        )
        page_resp = _api_get(index_url, token)
        for r in page_resp.get("results", []):
            total += 1
            if r.get("data", {}).get("status", {}).get("type") == "UP":
                total_up += 1
        if page >= page_resp.get("pageCount", 1):
            break
        page += 1

    return RealmStatus(
        realm_name=realm,
        realm_up=realm_up,
        total_up=total_up,
        total=total,
    )
