"""Token fetcher — 远端 hook 提供 24h token，内存缓存到次日本地 00:00。"""

from __future__ import annotations

import json
import os
import time
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

BASE_API_URL = "https://api.mingdao.com"
HOOK_URL = "https://api.mingdao.com/workflow/hooks2/NjlkYzQ5NGIwMzM0NzkwYjg4MWY4NTk5"
APPNAME = "mdcloud"

_cache: dict[str, Any] = {"token": "", "expires_at": 0}


def _load_env() -> None:
    """Lazy load .env from cwd or package parent."""
    for d in [Path.cwd(), Path(__file__).resolve().parent.parent.parent]:
        env = d / ".env"
        if not env.exists():
            continue
        for raw_line in env.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())
        return


def _next_local_midnight_ts() -> int:
    now = datetime.now()
    tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return int(tomorrow.timestamp())


def ensure_access_token() -> str:
    if _cache["token"] and time.time() < _cache["expires_at"] - 60:
        return str(_cache["token"])

    _load_env()
    account_id = os.getenv("MD_ACCOUNT_ID", "").strip()
    key = os.getenv("MD_KEY", "").strip()
    if not account_id or not key:
        raise RuntimeError(
            "Missing MD_ACCOUNT_ID or MD_KEY. Set them in .env or environment."
        )

    body = json.dumps(
        {"account_id": account_id, "key": key, "appname": APPNAME}
    ).encode("utf-8")
    req = urllib.request.Request(
        HOOK_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "md-cloud/0.1",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    token = data.get("token")
    if not token:
        raise RuntimeError(f"Token endpoint returned no token: {data!r}")

    _cache["token"] = token
    _cache["expires_at"] = _next_local_midnight_ts()
    return str(token)
