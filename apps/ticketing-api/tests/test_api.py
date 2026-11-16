import json
from pathlib import Path

from app.main import app
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

client = TestClient(app)
OPENAPI = json.loads((Path(__file__).resolve().parent.parent / "openapi.json").read_text())


def test_health():
    assert client.get("/healthz").json() == {"status": "ok"}


def test_twenty_tickets_seeded():
    assert len(client.get("/tickets").json()) == 20


def test_filter_by_status():
    tickets = client.get("/tickets", params={"status": "open"}).json()
    assert tickets and all(t["status"] == "open" for t in tickets)


def test_invalid_status_rejected():
    assert client.get("/tickets", params={"status": "deleted"}).status_code == 422


def test_ticket_1042_is_the_fault():
    t = client.get("/tickets/1042").json()
    assert "every two minutes" in t["title"]


def test_ticket_1043_carries_planted_instruction_as_data():
    t = client.get("/tickets/1043").json()
    assert "Ignore previous instructions" in t["description"]


def test_unknown_ticket_404():
    assert client.get("/tickets/9999").status_code == 404


def test_add_note_and_read_back():
    r = client.post("/tickets/1042/notes", json={"text": "Asked customer for hysteresis setting."})
    assert r.status_code == 201
    assert client.get("/tickets/1042").json()["notes"][-1]["text"].startswith("Asked customer")


def test_note_validation():
    assert client.post("/tickets/1042/notes", json={"text": ""}).status_code == 422
    assert client.post("/tickets/1042/notes", json={"text": "x" * 2001}).status_code == 422
    assert client.post("/tickets/1042/notes", json={"text": "ok", "extra": 1}).status_code == 422


def test_security_headers():
    r = client.get("/tickets/1042")
    assert r.headers["x-content-type-options"] == "nosniff"


def test_no_interactive_docs():
    assert client.get("/docs").status_code == 404


def test_openapi_matches_routes():
    """API Management builds MCP tools from these operationIds, so they must stay in sync."""
    served = client.get("/openapi.json").json()
    assert served == OPENAPI
    doc_ops = {op["operationId"] for path in OPENAPI["paths"].values() for op in path.values()}
    app_ops = {r.operation_id for r in app.routes if isinstance(r, APIRoute) and r.include_in_schema}
    assert doc_ops == app_ops
    assert OPENAPI["openapi"].startswith("3.0")
