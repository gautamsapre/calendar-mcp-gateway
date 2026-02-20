from __future__ import annotations

from typing import Any, Dict, List, Optional
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials


class PeopleClient:
    def __init__(self, creds: Credentials):
        # Avoid creating discovery cache files on disk
        self._service = build("people", "v1", credentials=creds, cache_discovery=False)

    def search_contacts(self, query: str, page_size: int = 5) -> List[Dict[str, Any]]:
        """
        Returns a ranked list of {display_name, email, resource_name, confidence}.
        Only returns entries that have emails.
        """
        resp = (
            self._service.people()
            .searchContacts(
                query=query,
                readMask="names,emailAddresses",
                pageSize=page_size,
            )
            .execute()
        )

        out: List[Dict[str, Any]] = []
        for r in resp.get("results", []) or []:
            person = r.get("person", {}) or {}
            resource_name = person.get("resourceName")

            names = person.get("names", []) or []
            emails = person.get("emailAddresses", []) or []

            display_name: Optional[str] = None
            if names:
                display_name = names[0].get("displayName")

            confidence = (r.get("searchResultMetadata") or {}).get("confidence")

            for e in emails:
                val = e.get("value")
                if val:
                    out.append(
                        {
                            "display_name": display_name or query,
                            "email": val,
                            "resource_name": resource_name,
                            "confidence": confidence,
                        }
                    )

        # de-dupe by email while keeping order
        seen = set()
        deduped = []
        for item in out:
            if item["email"] not in seen:
                seen.add(item["email"])
                deduped.append(item)

        return deduped[:page_size]