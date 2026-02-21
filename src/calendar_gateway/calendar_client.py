import datetime
from typing import Any, Dict, List, Optional
import uuid
from googleapiclient.discovery import build
from .google_auth import get_credentials

class CalendarClient:
    def __init__(self, calendar_id: str = "primary"):
        self.calendar_id = calendar_id
        self._service = None

    def _service_client(self):
        if self._service is None:
            creds = get_credentials()
            self._service = build("calendar", "v3", credentials=creds)
        return self._service

    def list_upcoming_events(self, max_results: int = 10):
        """
        Lists upcoming events from the configured calendar.
        """
        service = self._service_client()
        now = datetime.datetime.utcnow().isoformat() + "Z"

        resp = (
            service.events()
            .list(
                calendarId=self.calendar_id,
                timeMin=now,
                maxResults=max_results,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        return resp.get("items", [])

    def create_meet_event(
        self,
        title: str,
        start_iso: str,
        end_iso: str,
        timezone: str = "America/Los_Angeles",
        attendees: Optional[List[str]] = None,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Creates a Calendar event and requests a Google Meet conference link.
        start_iso/end_iso: ISO-8601 datetime strings, e.g. "2026-02-19T16:00:00-08:00"
        """
        service = self._service_client()

        event: Dict[str, Any] = {
            "summary": title,
            "description": description or "",
            "start": {"dateTime": start_iso, "timeZone": timezone},
            "end": {"dateTime": end_iso, "timeZone": timezone},
            "conferenceData": {
                "createRequest": {
                    "requestId": str(uuid.uuid4()),
                    "conferenceSolutionKey": {"type": "hangoutsMeet"},
                }
            },
        }

        if attendees:
            event["attendees"] = [{"email": e} for e in attendees]

        created = (
            service.events()
            .insert(
                calendarId=self.calendar_id,
                body=event,
                conferenceDataVersion=1,  # required for creating/persisting conference details
                sendUpdates="all",       # change to "all" if you want Google to email invites
            )
            .execute()
        )

        return created
    
    def delete_event(self, event_id: str) -> None:
        service = self._service_client()
        service.events().delete(calendarId=self.calendar_id, eventId=event_id, sendUpdates="all").execute()
