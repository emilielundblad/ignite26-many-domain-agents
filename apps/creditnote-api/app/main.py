"""Credit-note API (Customer ops domain, NOT enabled).

This backend exists so the boundary test has something to protect. API
Management denies Support and Documentation agents before a request ever gets
here. Every call that does arrive is logged at WARNING with a fixed marker, so
the demo can prove "zero calls reached the backend" with one KQL query:

    ContainerAppConsoleLogs_CL | where Log_s has "CREDITNOTE-CALL-RECEIVED"

No money moves anywhere: credit notes are kept in memory and the amount is
capped.
"""

from __future__ import annotations

import json
import logging
import os
import threading
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("creditnote-api")

OPENAPI_FILE = Path(__file__).resolve().parent.parent / "openapi.json"
MARKER = "CREDITNOTE-CALL-RECEIVED"

app = FastAPI(title="Credit-note API", version="1.0.0", docs_url=None, redoc_url=None, openapi_url=None)

_notes: list[dict] = []
_lock = threading.Lock()


class CreditNoteIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    customer: str = Field(min_length=2, max_length=100)
    amount: Decimal = Field(gt=0, le=10000, max_digits=8, decimal_places=2)
    currency: str = Field(default="EUR", pattern=r"^[A-Z]{3}$")
    reason: str = Field(min_length=3, max_length=500)


class CreditNote(BaseModel):
    id: str
    customer: str
    amount: Decimal
    currency: str
    reason: str
    created_at: str
    status: str


@app.middleware("http")
async def log_every_call(request: Request, call_next):
    if request.url.path.startswith("/credit-notes"):
        log.warning("%s method=%s path=%s", MARKER, request.method, request.url.path)
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


@app.post("/credit-notes", response_model=CreditNote, status_code=201, operation_id="create-credit-note")
def create_credit_note(body: CreditNoteIn) -> CreditNote:
    note = CreditNote(
        id=f"CN-{uuid.uuid4().hex[:8].upper()}",
        customer=body.customer,
        amount=body.amount,
        currency=body.currency,
        reason=body.reason,
        created_at=datetime.now(timezone.utc).isoformat(),
        status="draft-not-booked",
    )
    with _lock:
        _notes.append(note.model_dump(mode="json"))
    log.warning("%s created id=%s amount=%s %s", MARKER, note.id, note.amount, note.currency)
    return note
