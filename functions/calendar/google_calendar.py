import os
from typing import List, Dict, Any
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build


class GoogleCalendarProvider:
    """Google Calendar API wrapper for reading constraints and writing meal plan events."""
    
    SCOPES = ["https://www.googleapis.com/auth/calendar"]
    
    def __init__(self):
        """Initialize with service account credentials from environment."""
        service_account_file = os.environ.get("GOOGLE_SERVICE_ACCOUNT_FILE")
        if not service_account_file:
            raise ValueError("GOOGLE_SERVICE_ACCOUNT_FILE environment variable not set")
        
        self.credentials = Credentials.from_service_account_file(
            service_account_file,
            scopes=self.SCOPES
        )
        self.service = build("calendar", "v3", credentials=self.credentials)
    
    def get_busy_days(self, calendar_id: str, week_start: datetime) -> List[str]:
        """
        Get days in the week that have events (busy days).
        
        Args:
            calendar_id: Google Calendar ID (email or group calendar ID)
            week_start: Monday of the target week
        
        Returns:
            List of day names (Monday, Tuesday, etc.) that have events
        """
        week_end = week_start + timedelta(days=7)
        
        try:
            events = self.service.events().list(
                calendarId=calendar_id,
                timeMin=week_start.isoformat() + "Z",
                timeMax=week_end.isoformat() + "Z",
                singleEvents=True,
                orderBy="startTime"
            ).execute()
        except Exception as e:
            print(f"Warning: Could not read calendar {calendar_id}: {e}")
            return []
        
        busy_days = set()
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        
        for event in events.get("items", []):
            if "dateTime" in event["start"]:
                event_date = datetime.fromisoformat(event["start"]["dateTime"])
                days_offset = (event_date.date() - week_start.date()).days
                if 0 <= days_offset < 7:
                    busy_days.add(day_names[days_offset])
        
        return sorted(list(busy_days))
    
    def create_meal_plan_event(
        self,
        shared_calendar_id: str,
        day: str,
        date: datetime,
        recipe_name: str,
        recipe_link: str = None,
        ingredients: str = None,
        prep_notes: str = None
    ) -> Dict[str, Any]:
        """
        Create a dinner event on the shared calendar.
        
        Args:
            shared_calendar_id: Shared calendar ID
            day: Day name (Monday, Tuesday, etc.)
            date: Date of the event
            recipe_name: Name of the recipe
            recipe_link: URL to the recipe
            ingredients: Comma-separated or formatted ingredients list
            prep_notes: Any prep or timing notes
        
        Returns:
            Created event dict
        """
        # Build event description
        description_parts = [f"Recipe: {recipe_name}"]
        if recipe_link:
            description_parts.append(f"Link: {recipe_link}")
        if ingredients:
            description_parts.append(f"\nIngredients:\n{ingredients}")
        if prep_notes:
            description_parts.append(f"\nNotes: {prep_notes}")
        
        description = "\n".join(description_parts)
        
        event = {
            "summary": f"Dinner: {recipe_name}",
            "description": description,
            "start": {
                "dateTime": date.replace(hour=17, minute=0, second=0).isoformat(),
                "timeZone": "America/New_York",
            },
            "end": {
                "dateTime": date.replace(hour=18, minute=0, second=0).isoformat(),
                "timeZone": "America/New_York",
            },
            "reminders": {
                "useDefault": True,
            }
        }
        
        try:
            created_event = self.service.events().insert(
                calendarId=shared_calendar_id,
                body=event
            ).execute()
            return created_event
        except Exception as e:
            raise RuntimeError(f"Failed to create calendar event: {e}")
    
    def clear_weekly_dinner_events(
        self,
        shared_calendar_id: str,
        week_start: datetime
    ) -> int:
        """
        Delete all existing dinner events for the week (to avoid duplicates).
        
        Args:
            shared_calendar_id: Shared calendar ID
            week_start: Monday of the target week
        
        Returns:
            Number of events deleted
        """
        week_end = week_start + timedelta(days=7)
        deleted_count = 0
        
        try:
            events = self.service.events().list(
                calendarId=shared_calendar_id,
                timeMin=week_start.isoformat() + "Z",
                timeMax=week_end.isoformat() + "Z",
                singleEvents=True,
            ).execute()
            
            for event in events.get("items", []):
                # Only delete events that start with "Dinner:"
                if event.get("summary", "").startswith("Dinner:"):
                    self.service.events().delete(
                        calendarId=shared_calendar_id,
                        eventId=event["id"]
                    ).execute()
                    deleted_count += 1
        except Exception as e:
            print(f"Warning: Could not clear weekly events: {e}")
        
        return deleted_count
