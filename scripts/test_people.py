from calendar_gateway.google_auth import get_credentials
from calendar_gateway.people_client import PeopleClient

def main():
    creds = get_credentials()
    p = PeopleClient(creds)
    matches = p.search_contacts("Harsha", page_size=5)
    print(matches)

if __name__ == "__main__":
    main()