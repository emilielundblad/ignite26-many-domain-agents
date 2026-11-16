"""Minimal Microsoft Graph client for the setup scripts. Standard library only.

Tokens come from your own signed-in session (`azd auth login`, falling back to
`az login`), so the scripts act with exactly your delegated rights. Tokens are
never printed or written to disk.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

GRAPH = "https://graph.microsoft.com/v1.0"
_TOKENS: dict[str, tuple[str, float]] = {}


class GraphError(RuntimeError):
    def __init__(self, status: int, method: str, url: str, body: str):
        self.status = status
        self.body = body
        code = ""
        try:
            code = json.loads(body).get("error", {}).get("code", "")
        except (ValueError, AttributeError):
            pass
        self.code = code
        super().__init__(f"Graph {method} {url} failed: HTTP {status} {code}")


def _run(cmd: list[str]) -> str:
    exe = shutil.which(cmd[0])
    if not exe:
        raise FileNotFoundError(cmd[0])
    return subprocess.run([exe, *cmd[1:]], check=True, capture_output=True, text=True).stdout


def get_token(scope: str) -> str:
    """Access token for `scope` from azd, or from the Azure CLI as a fallback."""
    cached = _TOKENS.get(scope)
    if cached and cached[1] - time.time() > 300:
        return cached[0]
    errors = []
    try:
        out = json.loads(_run(["azd", "auth", "token", "--scope", scope, "--output", "json"]))
        token = out["token"]
    except (FileNotFoundError, subprocess.CalledProcessError, KeyError, ValueError) as exc:
        errors.append(f"azd: {type(exc).__name__}")
        try:
            resource = scope.removesuffix("/.default")
            token = _run(["az", "account", "get-access-token", "--resource", resource, "--query", "accessToken", "-o", "tsv"]).strip()
        except (FileNotFoundError, subprocess.CalledProcessError) as exc2:
            errors.append(f"az: {type(exc2).__name__}")
            sys.exit(f"Could not get a token for {scope} ({'; '.join(errors)}). Run `azd auth login` (or `az login`) first.")
    _TOKENS[scope] = (token, time.time() + 3000)
    return token


def request(method: str, path: str, body: Any | None = None, *, retries: int = 5, headers: dict | None = None) -> Any:
    """Call Graph. Retries throttling and the replication delay that follows object creation."""
    url = path if path.startswith("https://") else f"{GRAPH}{path}"
    # OData filters contain spaces and quotes; encode them but keep URL structure intact.
    url = urllib.parse.quote(url, safe=":/?&=$,'()@%+")
    data = json.dumps(body).encode() if body is not None else None
    for attempt in range(retries):
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("Authorization", f"Bearer {get_token('https://graph.microsoft.com/.default')}")
        req.add_header("Content-Type", "application/json")
        for k, v in (headers or {}).items():
            req.add_header(k, v)
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                raw = resp.read()
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as exc:
            text = exc.read().decode(errors="replace")
            retryable = exc.code in (429, 503, 504) or (exc.code in (400, 404) and "does not exist" in text)
            if retryable and attempt < retries - 1:
                time.sleep(min(30, int(exc.headers.get("Retry-After", 0) or 0) or 2 ** (attempt + 1)))
                continue
            raise GraphError(exc.code, method, url, text) from None
    raise RuntimeError("unreachable")


def quote(value: str) -> str:
    return urllib.parse.quote(value, safe="")
