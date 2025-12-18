from googleapiclient.discovery import build

def get_gmail_service(creds):
    return build('gmail', 'v1', credentials=creds)