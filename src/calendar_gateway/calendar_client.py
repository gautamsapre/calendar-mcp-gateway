import datetime
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
