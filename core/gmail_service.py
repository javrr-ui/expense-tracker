"""Gmail service utilities.

This module provides helper functions to create and configure the Gmail API service
client using authenticated credentials.
"""

from googleapiclient.discovery import build


def get_gmail_service(creds):
    """
    Build and return a Gmail API service client.

    Args:
        creds (google.oauth2.credentials.Credentials):
            Authenticated OAuth 2.0 credentials obtained from google_auth.get_credentials().

    Returns:
        googleapiclient.discovery.Resource:
            The Gmail API service object (v1) ready for making API calls.

    Example:
        >>> service = get_gmail_service(creds)
        >>> messages = service.users().messages().list(userId='me').execute()
    """
    return build("gmail", "v1", credentials=creds)
