"""Read and write values in the current azd environment."""

from __future__ import annotations

import json
import os
import shutil
import subprocess


def _azd(*args: str) -> str:
    exe = shutil.which("azd")
    if not exe:
        raise SystemExit("The Azure Developer CLI (azd) is required: https://aka.ms/azd-install")
    return subprocess.run([exe, *args], check=True, capture_output=True, text=True).stdout


def get_values() -> dict[str, str]:
    """azd environment values, overridden by real environment variables (azd hooks export them too)."""
    try:
        values = json.loads(_azd("env", "get-values", "--output", "json"))
    except (subprocess.CalledProcessError, ValueError):
        values = {}
    for key in list(values) + [k for k in os.environ if k.startswith(("AZURE_", "FOUNDRY_", "APIM_", "MCP_", "MODEL_", "IG26_", "LOG_ANALYTICS_"))]:
        if key in os.environ:
            values[key] = os.environ[key]
    return values


def require(values: dict[str, str], *keys: str) -> list[str]:
    missing = [k for k in keys if not values.get(k)]
    if missing:
        raise SystemExit(f"Missing azd environment values: {', '.join(missing)}. Run `azd up` first.")
    return [values[k] for k in keys]


def set_value(key: str, value: str) -> None:
    _azd("env", "set", key, value)
