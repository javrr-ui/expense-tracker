# auth.py
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# Define scopes here or pass them as needed
# Example: read-only access to contacts (People API)
SCOPES = ['https://www.googleapis.com/auth/contacts.readonly']

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CREDENTIALS_FILE = os.path.join(BASE_DIR, 'credentials.json')
TOKEN_FILE = os.path.join(BASE_DIR, 'token.json')

def get_credentials(scopes=None):
    """
    Performs Google OAuth 2.0 authentication and confirms success.
    Prints a clear message if connected successfully.
    Returns credentials if successful (for future use).
    """
    print("Starting Google authentication...")

    creds = None

    # Try to load existing token
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    # If no valid credentials, start OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing expired access token...")
            creds.refresh(Request())
        else:
            print("No valid credentials found. Opening browser for login...")
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        # Save new/updated token
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
        print(f"Token saved to {TOKEN_FILE}")

    print("✅ Google authentication successful!")
    print("   You are now connected to your Google account.")
    return creds