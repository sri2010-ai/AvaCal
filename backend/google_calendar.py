import os
import json
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

def create_google_calendar_client():
    """
    Creates and returns a Google Calendar API client using service account credentials.
    Credentials can be loaded from a file or an environment variable.
    """
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    
    # For deployment on Railway/Render, store the JSON content in an env var
    creds_json_str = os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON')
    
    if creds_json_str:
        creds_info = json.loads(creds_json_str)
        creds = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
    else:
        # For local development, read from the file
        creds = Credentials.from_service_account_file('service_account.json', scopes=SCOPES)
        
    service = build('calendar', 'v3', credentials=creds)
    return service