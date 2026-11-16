"""Offline tests for the setup scripts. No Azure or Graph calls are made."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from identity import graph, setup_gateway_app  # noqa: E402
from identity.assign_agent_roles import assign  # noqa: E402


def test_role_ids_are_stable_and_unique():
    ids = [setup_gateway_app.role_id(v) for v, _, _ in setup_gateway_app.APP_ROLES]
    assert len(set(ids)) == 3
    assert ids == [setup_gateway_app.role_id(v) for v, _, _ in setup_gateway_app.APP_ROLES]


def test_roles_are_application_only():
    for r in setup_gateway_app.desired_roles():
        assert r["allowedMemberTypes"] == ["Application"]


def test_role_values_match_bicep():
    bicep = (ROOT / "infra" / "resources.bicep").read_text()
    for value, _, _ in setup_gateway_app.APP_ROLES:
        assert f"appRole: '{value}'" in bicep


class FakeGraph:
    def __init__(self):
        self.calls = []
        self.apps = []
        self.sps = []
        self.assignments = []

    def __call__(self, method, path, body=None, **kw):
        self.calls.append((method, path, body))
        if method == "GET" and path.startswith("/applications?"):
            return {"value": self.apps}
        if method == "POST" and path == "/applications":
            app = {"id": "obj-1", "appId": "app-1", "appRoles": body["appRoles"], "identifierUris": [], "api": body["api"]}
            self.apps.append(app)
            return app
        if method == "PATCH" and path.startswith("/applications/"):
            self.apps[0].update(body)
            return None
        if method == "GET" and path.startswith("/applications/"):
            return self.apps[0]
        if method == "GET" and path.startswith("/servicePrincipals?"):
            return {"value": self.sps}
        if method == "POST" and path == "/servicePrincipals":
            sp = {"id": "sp-1", "appId": body["appId"], "appRoleAssignmentRequired": False}
            self.sps.append(sp)
            return sp
        if method == "PATCH" and path.startswith("/servicePrincipals/"):
            self.sps[0].update(body)
            return None
        if method == "GET" and path.endswith("/appRoleAssignments?$select=appRoleId,resourceId"):
            return {"value": [{"appRoleId": a["appRoleId"], "resourceId": a["resourceId"]} for a in self.assignments]}
        if method == "POST" and path.endswith("/appRoleAssignedTo"):
            self.assignments.append(body)
            return body
        raise AssertionError(f"unexpected call {method} {path}")


@pytest.fixture
def fake(monkeypatch):
    f = FakeGraph()
    monkeypatch.setattr(graph, "request", f)
    return f


def test_ensure_app_creates_then_reuses(fake):
    app = setup_gateway_app.ensure_app("ig26-mcp-gateway-test")
    assert app["identifierUris"] == ["api://app-1"]
    assert {r["value"] for r in app["appRoles"]} == {"Support.Tools", "Docs.Tools", "CustOps.Tools"}
    posts = [c for c in fake.calls if c[0] == "POST"]
    setup_gateway_app.ensure_app("ig26-mcp-gateway-test")
    assert [c for c in fake.calls if c[0] == "POST"] == posts  # nothing created the second time


def test_app_has_no_credentials(fake):
    setup_gateway_app.ensure_app("ig26-mcp-gateway-test")
    body = next(c[2] for c in fake.calls if c[0] == "POST" and c[1] == "/applications")
    assert "passwordCredentials" not in body and "keyCredentials" not in body


def test_service_principal_requires_assignment(fake):
    sp = setup_gateway_app.ensure_service_principal("app-1")
    assert fake.sps[0]["appRoleAssignmentRequired"] is True
    assert sp["id"] == "sp-1"


def test_assign_is_idempotent(fake):
    assert assign("sp-1", "agent-1", "Support.Tools") is True
    assert assign("sp-1", "agent-1", "Support.Tools") is False
    assert len(fake.assignments) == 1


def test_graph_error_parses_code():
    err = graph.GraphError(403, "GET", "https://graph.microsoft.com/v1.0/x", json.dumps({"error": {"code": "Authorization_RequestDenied"}}))
    assert err.code == "Authorization_RequestDenied"
    assert "Bearer" not in str(err)


def test_agent_specs_respect_domain_boundary():
    from agents.common import AGENTS, SERVER_LABELS

    names = {a.name for a in AGENTS}
    assert names == {"support-agent", "docs-agent"}  # no Customer ops agent: domain not enabled
    for a in AGENTS:
        assert "CustOps.Tools" not in a.app_roles
        assert all(s in SERVER_LABELS for s in a.mcp_servers)
    support = next(a for a in AGENTS if a.name == "support-agent")
    assert "mcp-custops-creditnotes" in support.mcp_servers  # configured on purpose for the boundary test


def test_build_definition_routes_tools_through_gateway():
    from agents.common import AGENTS
    from agents.setup_agents import build_definition

    d = build_definition(AGENTS[0], "ig26-models-support/gpt-4.1-mini", "https://apim.example.net")
    tools = d["tools"]
    assert {t["server_url"] for t in tools} == {f"https://apim.example.net/{s}/mcp" for s in AGENTS[0].mcp_servers}
    # Connection names are account-unique, so they carry the agent's project suffix.
    assert {t["project_connection_id"] for t in tools} == {f"{s}-{AGENTS[0].project}" for s in AGENTS[0].mcp_servers}
    assert all(t["require_approval"] == "never" for t in tools)


def test_connections_match_agent_servers():
    from agents.common import AGENTS

    bicep = (ROOT / "infra" / "resources.bicep").read_text()
    for a in AGENTS:
        for s in a.mcp_servers:
            assert f"mcpName: '{s}'" in bicep


def test_summarize_reports_denied_tool_call():
    from agents.common import summarize

    response = SimpleNamespace(
        id="resp_1",
        status="completed",
        output_text="The gateway denied it.",
        output=[
            SimpleNamespace(type="mcp_call", server_label="support_tickets", name="get-ticket", arguments="{}", error=None),
            SimpleNamespace(type="mcp_call", server_label="customer_ops_credit_notes", name="create-credit-note", arguments="{}", error="403 Forbidden"),
        ],
    )
    s = summarize(response)
    assert [c["outcome"] for c in s["tool_calls"]] == ["ok", "error"]


def test_hooks_reject_unknown_command(monkeypatch):
    sys.path.insert(0, str(ROOT / "scripts"))
    import hooks

    monkeypatch.setattr(sys, "argv", ["hooks.py", "nope"])
    with pytest.raises(SystemExit):
        hooks.main()


def test_gitignore_keeps_local_state_out():
    ignored = (ROOT / ".gitignore").read_text()
    for entry in (".ig26/", ".venv/", ".azure/"):
        assert entry in ignored


def test_demo1_masks_ids_for_recording():
    from identity.run_demo1 import mask

    masked = mask("principal 3f2b9c1e-1111-2222-3333-444455556666 holds Support.Tools")
    assert "3f2b****-****" in masked
    assert "444455556666" not in masked


def test_demo1_is_read_only(monkeypatch):
    from identity import graph as g
    from identity import run_demo1

    calls = []

    def fake(method, path, body=None, **kw):
        calls.append(method)
        if "conditionalAccess" in path:
            return {"value": [{"id": "x", "displayName": "ig26-block-custops-agents", "state": "enabledForReportingButNotEnforced"}]}
        if "appRoleAssignedTo" in path:
            return {"value": []}
        return {"displayName": "ig26-mcp-gateway-test", "appId": "a", "appRoleAssignmentRequired": True, "value": []}

    monkeypatch.setattr(g, "request", fake)
    out = run_demo1.Out(show_ids=False, pause=False)
    agents = [{"name": "support-agent", "project": "support", "instanceIdentity": {"principalId": "p", "clientId": "c"}, "blueprint": {"clientId": "b"}}]
    run_demo1.step1(out, agents)
    run_demo1.step2(out, agents)
    run_demo1.step3(out, "sp")
    run_demo1.step4(out)
    run_demo1.step5(out)
    assert set(calls) == {"GET"}
