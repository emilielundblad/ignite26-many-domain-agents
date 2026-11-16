"""azd lifecycle hooks (see azure.yaml). Standard library only, works on Windows,
macOS and Linux.

  preprovision : create or reuse the Entra app for the governed MCP gateway
  postdeploy   : create a local virtual environment from agents/requirements.txt
                 (hash-pinned) and create the agents

Skip the Entra step (for example, an admin created the app for you) with:
  azd env set IG26_SKIP_ENTRA_SETUP true
Skip agent creation with:
  azd env set IG26_SKIP_AGENT_SETUP true
"""

from __future__ import annotations

import os
import subprocess
import sys
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VENV = ROOT / ".venv"


def _flag(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in ("1", "true", "yes")


def _venv_python() -> Path:
    return VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def ensure_venv() -> Path:
    py = _venv_python()
    if not py.exists():
        print(f"Creating virtual environment in {VENV}")
        venv.EnvBuilder(with_pip=True).create(VENV)
    marker = VENV / ".ig26-requirements"
    req = ROOT / "agents" / "requirements.txt"
    if not marker.exists() or marker.read_text() != req.read_text():
        print("Installing hash-pinned Python dependencies")
        subprocess.run([str(py), "-m", "pip", "install", "--quiet", "--disable-pip-version-check", "--require-hashes", "-r", str(req)], check=True)
        marker.write_text(req.read_text())
    return py


def preprovision() -> None:
    if _flag("IG26_SKIP_ENTRA_SETUP"):
        if not os.getenv("MCP_GATEWAY_APP_ID"):
            sys.exit("IG26_SKIP_ENTRA_SETUP is set but MCP_GATEWAY_APP_ID is empty. Set it with `azd env set MCP_GATEWAY_APP_ID <appId>`.")
        print("Skipping Entra app setup (IG26_SKIP_ENTRA_SETUP).")
        return
    sys.path.insert(0, str(ROOT))
    from identity import setup_gateway_app

    setup_gateway_app.main()


def postdeploy() -> None:
    if _flag("IG26_SKIP_AGENT_SETUP"):
        print("Skipping agent setup (IG26_SKIP_AGENT_SETUP). Run `python -m agents.setup_agents` later.")
        return
    py = ensure_venv()
    subprocess.run([str(py), "-m", "agents.setup_agents"], check=True, cwd=ROOT)


def main() -> None:
    if sys.version_info < (3, 10):
        sys.exit("Python 3.10 or later is required.")
    if len(sys.argv) != 2 or sys.argv[1] not in ("preprovision", "postdeploy", "venv"):
        sys.exit("usage: python scripts/hooks.py preprovision|postdeploy|venv")
    {"preprovision": preprovision, "postdeploy": postdeploy, "venv": ensure_venv}[sys.argv[1]]()


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        sys.exit(exc.returncode)
