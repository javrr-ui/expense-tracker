# auth.py
import logging
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.labels",
]

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CREDENTIALS_FILE = os.path.join(BASE_DIR, "credentials.json")
TOKEN_FILE = os.path.join(BASE_DIR, "token.json")

logger = logging.getLogger("expense_tracker")


def get_credentials(scopes=None):
    """
    Performs Google OAuth 2.0 authentication and confirms success.
    Prints a clear message if connected successfully.
    Returns credentials if successful (for future use).
    """
    logger.info("Starting Google authentication")

    creds = None

    # Try to load existing token
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    # If no valid credentials, start OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            logger.info("Refreshing expired access token")
            creds.refresh(Request())
        else:
            logger.info("No valid credentials found. Opening browser for login")
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        # Save new/updated token
        with open(TOKEN_FILE, "w", encoding="utf-8") as token:
            token.write(creds.to_json())
        logger.info("Token saved to %s", TOKEN_FILE)

    logger.info("Google authentication successful")
    logger.info("You are now connected to your Google account.")
    return creds
