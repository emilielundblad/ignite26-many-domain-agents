# Step 0: Lab, repo and deploy identity (Claude Code)

> **Note:** the code these prompts produce is already in this repository. Use the prompt to rebuild a step from scratch, to extend it, or to show on stage how it was built.

Paste into Claude Code from the repo root.

---

Read CLAUDE.md first and follow it.

Goal: prepare this repo and the lab subscription so that every later step deploys from GitHub Actions with no stored secrets, and so that you (Claude Code) and GitHub Copilot work inside clear guardrails.

Context:
- Lab tenant and subscription are dedicated to this demo. Subscription ID: <subscription-id>. Tenant ID: <tenant-id>. Region: Sweden Central unless a service below is not available there; check and tell me.
- GitHub repo: <owner>/ignite26-many-domain-agents. It was created after 15 July 2026, so GitHub issues OIDC tokens with immutable, ID-based subject claims (`repo:owner@<owner_id>/repo@<repo_id>:...`). Read the Learn page "Migrate GitHub Actions federated credentials to immutable subjects" and the GitHub OIDC-in-Azure doc before you write the federated credential.

Do this, stopping for my approval at each checkpoint:

1. Scaffold the repo: `infra/` (Bicep, azd), `apps/`, `agents/`, `identity/`, `docs/`, `.github/workflows/`. Add `docs/demo-state.md`.
2. Plan the deploy identity: one user-assigned managed identity `id-ig26-deploy` in `rg-ig26-platform`, with a federated credential for this repo's `main` branch and one for the `demo` environment, using the immutable subject format. Get the owner and repo IDs with `gh api`. CHECKPOINT: show me the subject strings and the exact role assignments you propose. Target: Contributor on the demo resource groups only, plus Role Based Access Control Administrator with a condition that limits it to the specific built-in roles the later steps need and to principal type ServicePrincipal. No subscription-wide Owner.
3. Write the Bicep for steps 2 and the workflow `deploy.yml` using `azure/login` pinned to a full commit SHA, `id-token: write`, and environment protection on `demo` with me as required reviewer.
4. CHECKPOINT: show me the what-if. I deploy this first piece myself from my own session, because creating the deploy identity needs my privileges.
5. Update `docs/demo-state.md`.

Acceptance: a no-op workflow run logs in to Azure through OIDC with no secrets in the repo, and `az role assignment list --assignee <id-ig26-deploy>` shows only the scoped assignments we agreed.

Record nothing in this step.
