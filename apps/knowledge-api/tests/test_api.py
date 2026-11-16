import json
from pathlib import Path

from app.main import app
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

client = TestClient(app)
OPENAPI = json.loads((Path(__file__).resolve().parent.parent / "openapi.json").read_text())


def test_thirty_articles_with_stable_urls():
    from app.data import ARTICLES

    assert len(ARTICLES) == 30
    assert all(a["url"].startswith("https://docs.example.com/aurora/kb/KB") for a in ARTICLES.values())


def test_search_finds_short_cycling_fix():
    hits = client.get("/articles/search", params={"q": "heating on and off every two minutes hysteresis"}).json()
    assert hits[0]["id"] in {"KB0001", "KB0002"}
    assert hits[0]["url"].endswith(hits[0]["id"])


def test_search_limits():
    assert client.get("/articles/search", params={"q": "a"}).status_code == 422
    assert client.get("/articles/search", params={"q": "firmware", "top": 11}).status_code == 422
    assert len(client.get("/articles/search", params={"q": "firmware", "top": 2}).json()) <= 2


def test_get_article():
    a = client.get("/articles/KB0001").json()
    assert "hysteresis" in a["body"].lower()


def test_get_article_validation():
    assert client.get("/articles/KB9999").status_code == 404
    assert client.get("/articles/../../etc").status_code in (404, 422)
    assert client.get("/articles/kb1").status_code == 422


def test_openapi_matches_routes():
    assert client.get("/openapi.json").json() == OPENAPI
    doc_ops = {op["operationId"] for path in OPENAPI["paths"].values() for op in path.values()}
    app_ops = {r.operation_id for r in app.routes if isinstance(r, APIRoute) and r.include_in_schema}
    assert doc_ops == app_ops
