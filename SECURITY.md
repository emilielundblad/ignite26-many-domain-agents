# Security

This repository is demo and learning material. It deploys real Azure and Entra resources, so treat it with the same care as any infrastructure code.

## Reporting a vulnerability

Please do not open a public issue for security problems. Use GitHub's private vulnerability reporting on this repository (Security tab, "Report a vulnerability").

## Rules for contributions

- Never commit secrets, keys, connection strings, tenant IDs or subscription IDs.
- Use managed identities and workload identity federation; no client secrets.
- Keep Conditional Access policies in report-only mode in examples.
- Pin GitHub Actions to a full commit SHA.
- Use fake data only.

## Running it safely

- Use a dedicated lab tenant and subscription.
- Review every plan and what-if output the coding agents show you before approving.
- Run the teardown prompt when you are done.
