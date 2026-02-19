from calendar_gateway.calendar_client import CalendarClient

def main():
    client = CalendarClient(calendar_id="primary")

    created = client.create_meet_event(
        title="Calendar Gateway: Integration Sync",
        start_iso="2026-02-19T18:00:00-08:00",
        end_iso="2026-02-19T18:30:00-08:00",
        attendees=[],  # add emails if you want
        description="Created via Calendar gateway integration.",
    )

    meet_link = None
    conf = created.get("conferenceData", {})
    for ep in conf.get("entryPoints", []) or []:
        if ep.get("entryPointType") == "video":
            meet_link = ep.get("uri")
            break

    print("Created event:")
    print("  id:", created.get("id"))
    print("  htmlLink:", created.get("htmlLink"))
    print("  meet:", meet_link)

if __name__ == "__main__":
    main()
