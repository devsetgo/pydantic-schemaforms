from __future__ import annotations

import json
import os
from dataclasses import dataclass
import httpx2 as httpx


@dataclass(frozen=True)
class GeoLookupResult:
    country: str | None
    country_code: str | None
    region: str | None
    city: str | None
    lat: float | None
    lon: float | None
    raw_json: str


class GeoLookupError(RuntimeError):
    def __init__(
        self, message: str, *, status_code: int | None = None, raw_json: str | None = None
    ):
        super().__init__(message)
        self.status_code = status_code
        self.raw_json = raw_json


def _iplocation_base_url() -> str:
    return (os.environ.get("IP_GEO_IP_API_BASE_URL") or "https://api.iplocation.net").rstrip("/")


def _timeout_seconds() -> float:
    raw = os.environ.get("IP_GEO_TIMEOUT_SECONDS")
    try:
        if raw is None:
            return 1.5
        return max(0.2, float(raw))
    except Exception:
        return 1.5


async def fetch_ip_api(ip: str) -> GeoLookupResult:
    url = _iplocation_base_url()
    params = {"ip": ip}

    timeout = httpx.Timeout(_timeout_seconds())
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.get(url, params=params, headers={"Accept": "application/json"})

    raw_text = resp.text or ""
    status_code = resp.status_code

    # 429 needs special handling by the worker (backoff).
    if status_code == 429:
        raise GeoLookupError("rate_limited", status_code=status_code, raw_json=raw_text)

    if status_code < 200 or status_code >= 300:
        raise GeoLookupError(f"http_{status_code}", status_code=status_code, raw_json=raw_text)

    try:
        data = resp.json()
    except Exception:
        raise GeoLookupError("invalid_json", status_code=status_code, raw_json=raw_text)

    if not isinstance(data, dict):
        raise GeoLookupError("invalid_payload", status_code=status_code, raw_json=raw_text)

    # api.iplocation.net signals success with response_code "200" (string).
    if str(data.get("response_code") or "") != "200":
        msg = (data.get("response_message") or "fail").strip() or "fail"
        raise GeoLookupError(
            msg, status_code=status_code, raw_json=json.dumps(data, ensure_ascii=False)
        )

    raw_json = json.dumps(data, ensure_ascii=False)

    return GeoLookupResult(
        country=(data.get("country_name") or None),
        country_code=(data.get("country_code2") or None),
        region=None,
        city=None,
        lat=None,
        lon=None,
        raw_json=raw_json,
    )
