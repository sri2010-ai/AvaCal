import os
from datetime import datetime, timedelta
import pytz
from langchain_core.tools import tool
from google_calendar import create_google_calendar_client
TIMEZONE = "America/Los_Angeles" 
TZ = pytz.timezone(TIMEZONE)

@tool
def check_availability(date: str) -> str:
    """
    Checks for available 1-hour appointment slots on a given date (YYYY-MM-DD).
    Assumes working hours are 9 AM to 5 PM in the America/Los_Angeles timezone.
    Returns a list of available start times.
    """
    try:
        service = create_google_calendar_client()
        calendar_id = os.environ.get("CALENDAR_ID")
        day = datetime.strptime(date, "%Y-%m-%d").astimezone(TZ)
        start_of_day = day.replace(hour=9, minute=0, second=0, microsecond=0)
        end_of_day = day.replace(hour=17, minute=0, second=0, microsecond=0)
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=start_of_day.isoformat(),
            timeMax=end_of_day.isoformat(),
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        busy_slots = events_result.get('items', [])
        possible_slots = []
        current_time = start_of_day
        while current_time < end_of_day:
            possible_slots.append(current_time)
            current_time += timedelta(hours=1)
        available_slots = []
        for slot_start in possible_slots:
            slot_end = slot_start + timedelta(hours=1)
            is_available = True
            for event in busy_slots:
                event_start = datetime.fromisoformat(event['start'].get('dateTime')).astimezone(TZ)
                event_end = datetime.fromisoformat(event['end'].get('dateTime')).astimezone(TZ)
                if max(slot_start, event_start) < min(slot_end, event_end):
                    is_available = False
                    break
            if is_available:
                available_slots.append(slot_start.strftime("%-I:%M %p"))

        if not available_slots:
            return f"No 1-hour slots are available on {date}."
        
        return f"The following 1-hour slots are available on {date}: {', '.join(available_slots)}"

    except Exception as e:
        return f"An error occurred while checking availability: {e}. Please ensure the date is in YYYY-MM-DD format."

@tool
def create_appointment(start_time: str, summary: str) -> str:
    """
    Books a 1-hour appointment on the calendar at a specified start time with a given summary.
    The start_time must be in ISO 8601 format with timezone (e.g., '2024-07-30T14:00:00-07:00').
    The summary is the title of the event.
    """
    try:
        service = create_google_calendar_client()
        calendar_id = os.environ.get("CALENDAR_ID")

        start = datetime.fromisoformat(start_time)
        end = start + timedelta(hours=1)

        event = {
            'summary': summary,
            'start': {'dateTime': start.isoformat(), 'timeZone': TIMEZONE},
            'end': {'dateTime': end.isoformat(), 'timeZone': TIMEZONE},
        }

        created_event = service.events().insert(calendarId=calendar_id, body=event).execute()
        
        return f"Success! Appointment '{summary}' has been booked for {start.strftime('%A, %B %d at %-I:%M %p')}. Event ID: {created_event.get('id')}"

    except Exception as e:
        return f"An error occurred while creating the appointment: {e}. Please ensure the start_time is in the correct ISO 8601 format."
