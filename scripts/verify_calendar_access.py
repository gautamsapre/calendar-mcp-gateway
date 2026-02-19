from calendar_gateway.calendar_client import CalendarClient

def main():
    client = CalendarClient(calendar_id="primary")
    events = client.list_upcoming_events(max_results=10)

    if not events:
        print("Calendar access verified. No upcoming events found.")
        return

    print("Calendar access verified. Upcoming events:")
    for e in events:
        start = e["start"].get("dateTime", e["start"].get("date"))
        title = e.get("summary", "(no title)")
        print(f"- {start}  |  {title}")

if __name__ == "__main__":
    main()
