# Deploying from GitHub Actions (optional)

The quick start deploys from your own session with `azd up`. This page sets up `.github/workflows/deploy.yml` so later infrastructure and app changes deploy from GitHub, with no secrets stored in GitHub.

The pipeline does **not** create Entra objects or agents. Those need a person's Entra rights and stay with `azd up` from your session.

1. Run `azd up` once from your session (creates the gateway app and the agents).
2. Read your repository's OIDC subject claim. Repositories created after 15 July 2026 use immutable, ID-based subjects:
   ```bash
   gh api repos/<owner>/<repo>/actions/oidc/customization/sub
   ```
   Build the subject for the `demo` environment as described in GitHub's OpenID Connect documentation.
3. Deploy the identity (you need Owner or User Access Administrator on the subscription):
   ```bash
   az deployment sub what-if --location swedencentral --template-file infra/bootstrap/deploy-identity.bicep \
     --parameters environmentName=<env> githubOidcSubject='<subject>'
   az deployment sub create  --location swedencentral --template-file infra/bootstrap/deploy-identity.bicep \
     --parameters environmentName=<env> githubOidcSubject='<subject>'
   ```
   It creates `id-ig26-deploy` with Contributor and a constrained RBAC Administrator on the lab resource group, and a custom role at subscription scope that can only run deployments.
4. In GitHub: Settings > Environments > New environment `demo`, add yourself as required reviewer, and add these **variables**: `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID` (outputs of step 3), `AZURE_ENV_NAME`, `AZURE_LOCATION`, `MCP_GATEWAY_APP_ID` (from `azd env get-values`).
5. Turn on secret scanning and push protection (Settings > Code security), and protect `main` with required reviews and the `ci` checks.
6. Actions > deploy > Run workflow. It shows a what-if, then provisions and deploys after your approval of the environment.
