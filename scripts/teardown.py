"""Remove everything this lab created. You run this yourself; nothing calls it.

Order:
  1. azd down: deletes the resource group (all Azure resources, including the
     Foundry projects; Foundry removes the agent identities and blueprints it
     created with them).
  2. Purge the soft-deleted Foundry and Content Safety accounts and the
     soft-deleted API Management instance, so names and model quota are freed.
  3. Delete the Entra app registration for the MCP gateway (this also removes its
     service principal and every app role assignment to it).
Key Vault has purge protection on: it stays soft-deleted for 7 days, then goes.
Not removed (you created them by hand for Demo 1): Conditional Access policies and
the policy plan, sponsors, lifecycle policies. Delete those in the portal.

    python scripts/teardown.py            # shows the plan, asks you to type the env name
    python scripts/teardown.py --dry-run  # shows the plan only
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from identity.azd_env import get_values  # noqa: E402


def run(cmd: list[str], *, check: bool = True) -> int:
    exe = shutil.which(cmd[0])
    if not exe:
        sys.exit(f"{cmd[0]} not found on PATH")
    print("$ " + " ".join(cmd))
    return subprocess.run([exe, *cmd[1:]], check=check).returncode


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    v = get_values()
    env_name = v.get("AZURE_ENV_NAME", "")
    plan = [
        f"Delete resource group {v.get('AZURE_RESOURCE_GROUP', '(unknown)')} with azd down",
        f"Purge Foundry account {v.get('FOUNDRY_ACCOUNT_NAME', '(unknown)')} and the Content Safety account",
        f"Purge API Management instance {v.get('APIM_NAME', '(unknown)')}",
        f"Delete Entra app registration with appId {v.get('MCP_GATEWAY_APP_ID', '(unknown)')}",
    ]
    print("Teardown plan:")
    for i, p in enumerate(plan, 1):
        print(f"  {i}. {p}")
    print("Not included: the Demo 1 Conditional Access policies, policy plan, sponsors and lifecycle policy. Remove them in the portal.")
    print("These deletions cannot be undone.")
    if args.dry_run:
        return
    if not env_name or input(f"Type the environment name ({env_name}) to continue: ").strip() != env_name:
        sys.exit("Cancelled.")

    location = v.get("AZURE_LOCATION", "")
    rg = v.get("AZURE_RESOURCE_GROUP", "")
    foundry = v.get("FOUNDRY_ACCOUNT_NAME", "")
    apim = v.get("APIM_NAME", "")
    token = foundry.removeprefix("aif-ig26-")

    run(["azd", "down", "--force"])
    for account in filter(None, [foundry, f"cs-ig26-{token}" if token else ""]):
        run(["az", "cognitiveservices", "account", "purge", "--name", account, "--resource-group", rg, "--location", location], check=False)
    if apim:
        run(["az", "apim", "deletedservice", "purge", "--service-name", apim, "--location", location], check=False)
    if v.get("MCP_GATEWAY_APP_ID"):
        run(["az", "ad", "app", "delete", "--id", v["MCP_GATEWAY_APP_ID"]], check=False)
    print("Done. Remove the local .ig26 and .venv folders if you like.")


if __name__ == "__main__":
    main()
