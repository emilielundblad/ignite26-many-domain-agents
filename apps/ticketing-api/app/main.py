"""Ticketing API (Support domain). Fake data, in-memory notes.

Runs as an internal Container App. It is reachable only through API Management,
which exposes it as the MCP server `mcp-support-tickets`.
"""

from __future__ import annotations

import json
import logging
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi import Path as PathParam
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from .data import TICKETS

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("ticketing-api")

OPENAPI_FILE = Path(__file__).resolve().parent.parent / "openapi.json"

app = FastAPI(
    title="Ticketing API",
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,  # the curated OpenAPI document is served below
)

_notes: dict[int, list[dict]] = {}
_lock = threading.Lock()

Status = Literal["open", "pending", "closed"]


class Ticket(BaseModel):
    id: int
    title: str
    description: str
    customer: str
    product: str
    status: Status
    notes: list[dict] = Field(default_factory=list)


class NoteIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(min_length=1, max_length=2000)


class Note(BaseModel):
    ticket_id: int
    text: str
    created_at: str


def _ticket(ticket_id: int) -> Ticket:
    raw = TICKETS.get(ticket_id)
    if raw is None:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
    with _lock:
        notes = list(_notes.get(ticket_id, []))
    return Ticket(id=ticket_id, notes=notes, **raw)


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


@app.get("/tickets", response_model=list[Ticket], operation_id="list-tickets")
def list_tickets(status: Status | None = Query(default=None)) -> list[Ticket]:
    ids = sorted(t for t, v in TICKETS.items() if status is None or v["status"] == status)
    return [_ticket(t) for t in ids]


@app.get("/tickets/{ticket_id}", response_model=Ticket, operation_id="get-ticket")
def get_ticket(ticket_id: int = PathParam(ge=1, le=999999)) -> Ticket:
    log.info("get-ticket id=%s", ticket_id)
    return _ticket(ticket_id)


@app.post("/tickets/{ticket_id}/notes", response_model=Note, status_code=201, operation_id="add-ticket-note")
def add_note(note: NoteIn, ticket_id: int = PathParam(ge=1, le=999999)) -> Note:
    _ticket(ticket_id)
    created = Note(ticket_id=ticket_id, text=note.text, created_at=datetime.now(timezone.utc).isoformat())
    with _lock:
        _notes.setdefault(ticket_id, []).append({"text": created.text, "created_at": created.created_at})
    log.info("add-ticket-note id=%s length=%s", ticket_id, len(note.text))
    return created
