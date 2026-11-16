"""Knowledge API (Documentation domain). Fake product articles with stable URLs.

Runs as an internal Container App, exposed through API Management as the MCP
server `mcp-docs-knowledge`. Support agents also get read access to it in the
pattern; that grant is an app role assignment, not a code change here.
"""

from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi import Path as PathParam
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .data import ARTICLES

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("knowledge-api")

OPENAPI_FILE = Path(__file__).resolve().parent.parent / "openapi.json"

app = FastAPI(title="Knowledge API", version="1.0.0", docs_url=None, redoc_url=None, openapi_url=None)


class Article(BaseModel):
    id: str
    title: str
    body: str
    tags: list[str]
    url: str


class SearchHit(BaseModel):
    id: str
    title: str
    url: str
    score: int
    snippet: str


_WORD = re.compile(r"[a-z0-9.]+")


def _score(query: str, article: dict) -> int:
    words = set(_WORD.findall(query.lower()))
    if not words:
        return 0
    title = article["title"].lower()
    body = article["body"].lower()
    tags = " ".join(article["tags"]).lower()
    score = 0
    for w in words:
        if len(w) < 3:
            continue
        score += 5 * title.count(w) + 3 * tags.count(w) + body.count(w)
    return score


@app.middleware("http")
async def security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/healthz", include_in_schema=False)
def healthz() -> dict:
    return {"status": "ok"}


@app.get("/openapi.json", include_in_schema=False)
def openapi_document() -> JSONResponse:
    return JSONResponse(json.loads(OPENAPI_FILE.read_text(encoding="utf-8")))


@app.get("/articles/search", response_model=list[SearchHit], operation_id="search-articles")
def search_articles(
    q: str = Query(min_length=2, max_length=200),
    top: int = Query(default=5, ge=1, le=10),
) -> list[SearchHit]:
    hits = []
    for a in ARTICLES.values():
        s = _score(q, a)
        if s > 0:
            hits.append(SearchHit(id=a["id"], title=a["title"], url=a["url"], score=s, snippet=a["body"][:160]))
    hits.sort(key=lambda h: (-h.score, h.id))
    log.info("search-articles q_length=%s hits=%s", len(q), len(hits))
    return hits[:top]


@app.get("/articles/{article_id}", response_model=Article, operation_id="get-article")
def get_article(article_id: str = PathParam(pattern=r"^KB\d{4}$")) -> Article:
    a = ARTICLES.get(article_id)
    if a is None:
        raise HTTPException(status_code=404, detail=f"Article {article_id} not found")
    return Article(**a)
