import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

DEFAULT_SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/contacts.readonly",
]

# ✅ Always locate creds relative to this file, not the current working directory
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_DEFAULT_CREDENTIALS_PATH = os.path.join(_BASE_DIR, "..", "..", "credentials.json")
_DEFAULT_TOKEN_PATH = os.path.join(_BASE_DIR, "..", "..", "token.json")

def get_credentials(
    scopes=DEFAULT_SCOPES,
    credentials_path: str = _DEFAULT_CREDENTIALS_PATH,
    token_path: str = _DEFAULT_TOKEN_PATH,
):
    creds = None
    credentials_path = os.path.abspath(credentials_path)
    token_path = os.path.abspath(token_path)

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, scopes)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(credentials_path):
                raise FileNotFoundError(
                    f"Missing credentials.json at: {credentials_path}. "
                    f"Put your OAuth client file there (or pass credentials_path)."
                )
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, scopes)
            creds = flow.run_local_server(port=0)

        with open(token_path, "w") as f:
            f.write(creds.to_json())

    return creds