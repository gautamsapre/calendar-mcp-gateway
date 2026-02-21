from __future__ import annotations

import os
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from calendar_gateway.calendar_client import CalendarClient
from calendar_gateway.google_auth import get_credentials
from calendar_gateway.people_client import PeopleClient

API_KEY = os.environ.get("CALGW_API_KEY", "")

app = FastAPI(title="calendar-gateway-http")

from fastapi import Request

@app.get("/debug_headers")
def debug_headers(request: Request):
    # Don't return secrets — only whether headers exist
    hdrs = {k.lower(): "present" for k in request.headers.keys()}
    return {
        "has_x_api_key": "x-api-key" in hdrs,
        "has_authorization": "authorization" in hdrs,
        "header_names_seen": sorted(list(hdrs.keys()))[:30],  # keep it short
    }

def _auth(
    x_api_key: str | None,
    authorization: str | None,
):
    # If you don't set CALGW_API_KEY, auth is disabled
    if not API_KEY:
        return

    # Accept x-api-key: <key>
    if x_api_key == API_KEY:
        return

    # Accept Authorization: Bearer <key>
    if authorization:
        parts = authorization.split()
        if len(parts) == 2 and parts[0].lower() == "bearer" and parts[1] == API_KEY:
            return

    raise HTTPException(status_code=401, detail="Unauthorized")

def _cal() -> CalendarClient:
    return CalendarClient(calendar_id="primary")

def _people() -> PeopleClient:
    creds = get_credentials()
    return PeopleClient(creds)

class ResolveReq(BaseModel):
    name: str
    max_results: int = 5

class ScheduleReq(BaseModel):
    title: str
    start_iso: str
    end_iso: str
    timezone: str = "America/Los_Angeles"
    attendees: List[str] = []
    description: Optional[str] = None
    send_invites: bool = True

@app.get("/health")
def health():
    return {"ok": True}


@app.post("/resolve_contact")
def resolve_contact(
    req: ResolveReq,
    x_api_key: str | None = Header(default=None),
    authorization: str | None = Header(default=None),
):
    _auth(x_api_key, authorization)
    matches = _people().search_contacts(req.name, page_size=req.max_results)
    return {"query": req.name, "matches": matches}

@app.post("/schedule")
def schedule(req: ScheduleReq,     
    x_api_key: str | None = Header(default=None),
    authorization: str | None = Header(default=None)):
    _auth(x_api_key, authorization)
    c = _cal()
    created = c.create_meet_event(
        title=req.title,
        start_iso=req.start_iso,
        end_iso=req.end_iso,
        timezone=req.timezone,
        attendees=req.attendees,
        description=req.description,
        # you'll wire sendUpdates inside calendar_client via a param (see below)
    )
    return {"event_id": created.get("id"), "htmlLink": created.get("htmlLink"), "conferenceData": created.get("conferenceData")}