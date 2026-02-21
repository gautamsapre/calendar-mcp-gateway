from __future__ import annotations

import json
import os
import time
import uuid
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP

import warnings

# Keep STDIO channel clean. Warnings/logs must not interfere with protocol.
warnings.filterwarnings("ignore", category=FutureWarning, module=r"google\.api_core\._python_version_support")


from calendar_gateway.calendar_client import CalendarClient
from calendar_gateway.google_auth import get_credentials
from calendar_gateway.people_client import PeopleClient

mcp = FastMCP("calendar-gateway")

PENDING_FILE = os.path.join(os.getcwd(), "pending_cancels.json")
AUDIT_FILE = os.path.join(os.getcwd(), "audit_log.jsonl")

from pathlib import Path

def _data_dir() -> Path:
    # Allow override if you ever want it
    base = os.environ.get("CALGW_DATA_DIR")
    if base:
        p = Path(base).expanduser()
    else:
        p = Path.home() / ".calendar-mcp-gateway"
    p.mkdir(parents=True, exist_ok=True)
    return p

DATA_DIR = _data_dir()
PENDING_FILE = str(DATA_DIR / "pending_cancels.json")
AUDIT_FILE = str(DATA_DIR / "audit_log.jsonl")

def _audit(event: Dict[str, Any]) -> None:
    event = {**event, "ts": time.time()}
    with open(AUDIT_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")


def _load_pending() -> Dict[str, Any]:
    if not os.path.exists(PENDING_FILE):
        return {}
    try:
        with open(PENDING_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}


def _save_pending(data: Dict[str, Any]) -> None:
    with open(PENDING_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _client() -> CalendarClient:
    # Uses your existing OAuth token.json + credentials.json
    return CalendarClient(calendar_id="primary")


@mcp.tool()
def list_upcoming_events(max_results: int = 10) -> List[Dict[str, Any]]:
    """
    List upcoming calendar events for the authenticated user.

    Returns a list of normalized event objects with:
    - id
    - summary
    - start
    - end
    - htmlLink
    """
    c = _client()
    events = c.list_upcoming_events(max_results=max_results)

    normalized = []
    for e in events:
        normalized.append(
            {
                "id": e.get("id"),
                "summary": e.get("summary", "(no title)"),
                "start": e.get("start", {}),
                "end": e.get("end", {}),
                "htmlLink": e.get("htmlLink"),
            }
        )

    _audit({"tool": "list_upcoming_events", "max_results": max_results, "count": len(normalized)})
    return normalized


@mcp.tool()
def create_meet_event(
    title: str,
    start_iso: str,
    end_iso: str,
    timezone: str = "America/Los_Angeles",
    attendees: Optional[List[str]] = None,
    description: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create a calendar event with an attached Google Meet conference.

    start_iso/end_iso are ISO-8601 datetime strings, e.g.:
    2026-02-19T18:00:00-08:00
    """
    c = _client()
    created = c.create_meet_event(
        title=title,
        start_iso=start_iso,
        end_iso=end_iso,
        timezone=timezone,
        attendees=attendees or [],
        description=description,
    )

    meet_link = None
    conf = created.get("conferenceData", {}) or {}
    for ep in conf.get("entryPoints", []) or []:
        if ep.get("entryPointType") == "video":
            meet_link = ep.get("uri")
            break

    result = {
        "event_id": created.get("id"),
        "htmlLink": created.get("htmlLink"),
        "meet_link": meet_link,
    }

    _audit({"tool": "create_meet_event", "title": title, "start_iso": start_iso, "end_iso": end_iso})
    return result


@mcp.tool()
def request_cancel_event(event_id: str, reason: str) -> Dict[str, Any]:
    """
    Request cancellation of a calendar event.

    This tool does NOT delete the event.
    It creates a pending cancellation record that must be approved explicitly.
    """
    c = _client()

    # Minimal existence check: list a small window and match id (keeps Phase 3 simple)
    events = c.list_upcoming_events(max_results=50)
    match = next((e for e in events if e.get("id") == event_id), None)
    if not match:
        _audit({"tool": "request_cancel_event", "event_id": event_id, "status": "not_found"})
        return {"status": "rejected", "message": "Event not found in upcoming window."}

    pending_id = str(uuid.uuid4())
    pending = _load_pending()
    pending[pending_id] = {
        "event_id": event_id,
        "reason": reason,
        "summary": match.get("summary", "(no title)"),
        "start": match.get("start", {}),
        "htmlLink": match.get("htmlLink"),
        "created_at": time.time(),
    }
    _save_pending(pending)

    _audit({"tool": "request_cancel_event", "event_id": event_id, "pending_id": pending_id, "status": "pending"})
    return {
        "status": "pending",
        "pending_id": pending_id,
        "event_preview": {
            "summary": match.get("summary", "(no title)"),
            "start": match.get("start", {}),
            "htmlLink": match.get("htmlLink"),
        },
        "next_step": "Call approve_cancel(pending_id) to execute the cancellation.",
    }


@mcp.tool()
def approve_cancel(pending_id: str) -> Dict[str, Any]:
    """
    Approve and execute a pending cancellation.
    This performs the destructive action (event deletion).
    """
    pending = _load_pending()
    item = pending.get(pending_id)
    if not item:
        _audit({"tool": "approve_cancel", "pending_id": pending_id, "status": "not_found"})
        return {"status": "rejected", "message": "Pending cancellation not found."}

    c = _client()
    # You’ll implement delete_event in Phase 3 if not already present
    c.delete_event(item["event_id"])

    # Remove from pending store after success
    pending.pop(pending_id, None)
    _save_pending(pending)

    _audit({"tool": "approve_cancel", "pending_id": pending_id, "event_id": item["event_id"], "status": "executed"})
    return {"status": "executed", "event_id": item["event_id"]}

def _people() -> PeopleClient:
    creds = get_credentials()  # uses your shared token.json
    return PeopleClient(creds)

@mcp.tool()
def resolve_contact(name: str, max_results: int = 5) -> Dict[str, Any]:
    """
    Resolve a human name to likely email addresses (ranked).
    Safe tool: read-only, but still audited.
    """
    p = _people()
    matches = p.search_contacts(query=name, page_size=max_results)

    _audit({"tool": "resolve_contact", "query": name, "count": len(matches)})

    return {
        "query": name,
        "matches": matches,
        "rule": "If multiple matches are returned, ask the user to confirm which email to use before inviting.",
    }

@mcp.tool()
def ping() -> str:
    return "ok"

def main():
    mcp.run()

if __name__ == "__main__":
    main()