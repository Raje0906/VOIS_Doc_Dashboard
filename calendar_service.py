import os.path
import datetime
import pytz
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar']

class CalendarService:
    def __init__(self, credentials_path="credentials.json", token_path="token.json"):
        self.creds = None
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.credentials_path = os.path.join(self.base_dir, credentials_path)
        self.token_path = os.path.join(self.base_dir, token_path)
        self.service = None
        self.authenticate()

    def authenticate(self):
        """Authenticate with Google Calendar API"""
        import json
        
        # 1. Try Loading Token from Environment (for Vercel)
        token_json_env = os.getenv("GOOGLE_TOKEN_JSON")
        if token_json_env:
            try:
                info = json.loads(token_json_env)
                self.creds = Credentials.from_authorized_user_info(info, SCOPES)
            except Exception as e:
                print(f"Error loading token from env: {e}")
        
        # 2. Try Loading Token from File (Local)
        if not self.creds and os.path.exists(self.token_path):
            try:
                self.creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
            except Exception as e:
                print(f"Error loading token.json: {e}")
                self.creds = None

        # 3. Refresh if expired
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                try:
                    self.creds.refresh(Request())
                except Exception as e:
                    print(f"Error refreshing token: {e}")
                    self.creds = None
            
            # 4. If still no valid creds, try OAuth flow (Local only)
            if not self.creds:
                # Check Env for Credentials first
                creds_json_env = os.getenv("GOOGLE_CREDENTIALS_JSON")
                
                if creds_json_env:
                     # We cannot run InstalledAppFlow on Vercel (headless), so this path is mostly for local env vars
                     # But effectively, if we don't have a valid token on Vercel, we can't do much.
                     print("Warning: No valid token found in env. Cannot run auth flow in headless environment.")
                elif os.path.exists(self.credentials_path):
                    try:
                        flow = InstalledAppFlow.from_client_secrets_file(
                            self.credentials_path, SCOPES)
                        self.creds = flow.run_local_server(port=0)
                        # Save the credentials for the next run
                        with open(self.token_path, 'w') as token:
                            token.write(self.creds.to_json())
                    except Exception as e:
                        print(f"Error during OAuth flow: {e}")
                        return
                else:
                    print(f"Warning: {self.credentials_path} not found.")
                    return

        try:
            self.service = build('calendar', 'v3', credentials=self.creds)
        except Exception as e:
            print(f"Error building calendar service: {e}")
            self.service = None

    def _get_events_for_day(self, date_str):
        """Helper to get all events for a specific day"""
        if not self.service: return []
        try:
            # Get Calendar Timezone
            calendar_info = self.service.calendars().get(calendarId='primary').execute()
            tz_name = calendar_info.get('timeZone', 'UTC')
            tz = pytz.timezone(tz_name)
            
            target_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
            day_start = tz.localize(datetime.datetime.combine(target_date, datetime.time(0, 0)))
            day_end = tz.localize(datetime.datetime.combine(target_date, datetime.time(23, 59, 59)))
            
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=day_start.isoformat(),
                timeMax=day_end.isoformat(),
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            return events_result.get('items', [])
        except Exception as e:
            print(f"Error fetching events: {e}")
            return []

    def _generate_shift_slots(self):
        """Generates 30-min slots for Morning (10-1) and Evening (5-9)"""
        slots = []
        # Morning: 10:00 to 13:00 (last slot starts at 12:30)
        curr = datetime.datetime.strptime("10:00", "%H:%M")
        end = datetime.datetime.strptime("13:00", "%H:%M")
        while curr < end:
            slots.append(curr.strftime("%H:%M"))
            curr += datetime.timedelta(minutes=30)
            
        # Evening: 17:00 to 21:00 (last slot starts at 20:30)
        curr = datetime.datetime.strptime("17:00", "%H:%M")
        end = datetime.datetime.strptime("21:00", "%H:%M")
        while curr < end:
            slots.append(curr.strftime("%H:%M"))
            curr += datetime.timedelta(minutes=30)
            
        return slots

    def get_slot_status(self, date_str):
        """
        Returns status of the slots for the doctor dashboard.
        Status: 'available', 'booked', 'blocked'
        Returns a dict: { time: { 'status': '...', 'details': '...' } }
        """
        events = self._get_events_for_day(date_str)
        generated_slots = self._generate_shift_slots()
        status_map = {}
        
        # Get Calendar Timezone
        try:
             calendar_info = self.service.calendars().get(calendarId='primary').execute()
             tz_name = calendar_info.get('timeZone', 'UTC')
             tz = pytz.timezone(tz_name)
        except:
             tz = pytz.UTC

        now = datetime.datetime.now(tz)
        today_str = now.strftime("%Y-%m-%d")

        for time_str in generated_slots:
            slot_data = {'status': 'available', 'details': ''}

            # CHECK 1: If date is today, check if time is past
            if date_str == today_str:
                slot_dt = datetime.datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
                slot_dt = tz.localize(slot_dt) # Assume slot is in calendar timezone
                if slot_dt < now:
                    slot_data['status'] = 'blocked' # Mark as blocked/unavailable
                    slot_data['details'] = 'Past time'
            
            # CHECK 2: Check against actual events (overrides past check if booked)
            for event in events:
                start = event['start'].get('dateTime')
                if not start: continue
                
                try:
                    e_start = datetime.datetime.fromisoformat(start)
                    # Check if event starts *at* this slot time
                    if e_start.strftime("%H:%M") == time_str:
                         summary = event.get('summary', '')
                         if summary == 'BLOCKED':
                             slot_data['status'] = 'blocked'
                         else:
                             slot_data['status'] = 'booked'
                             # Extract patient name from "Appointment: Name" if possible
                             if summary.startswith("Appointment: "):
                                 slot_data['details'] = summary.replace("Appointment: ", "")
                             else:
                                 slot_data['details'] = summary
                         break
                except:
                    continue
            
            status_map[time_str] = slot_data
            
        return status_map

    def get_available_slots(self, date_str):
        """Returns ONLY the available slots for the patient"""
        status_map = self.get_slot_status(date_str)
        return [slot for slot, data in status_map.items() if data['status'] == 'available']

    def toggle_slot(self, date_str, time_str, action):
        """
        Action: 'block' (mark unavailable), 'unblock' (mark available)
        """
        if not self.service: return False, "Service not init"
        
        try:
            # Get Calendar Timezone
            calendar_info = self.service.calendars().get(calendarId='primary').execute()
            tz_name = calendar_info.get('timeZone', 'UTC')
            tz = pytz.timezone(tz_name)

            if action == 'block':
                # Create a "BLOCKED" event
                start_dt = datetime.datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
                # Localize to calendar timezone
                start_dt = tz.localize(start_dt)
                end_dt = start_dt + datetime.timedelta(minutes=30)
                
                event = {
                    'summary': 'BLOCKED',
                    'start': {'dateTime': start_dt.isoformat()},
                    'end': {'dateTime': end_dt.isoformat()}
                }
                self.service.events().insert(calendarId='primary', body=event).execute()
                return True, "Slot blocked"
                
            elif action == 'unblock':
                # Find the BLOCKED event and delete it
                events = self._get_events_for_day(date_str)
                for event in events:
                    if event.get('summary') == 'BLOCKED':
                        start = event['start'].get('dateTime')
                        if start: 
                             try:
                                 e_start = datetime.datetime.fromisoformat(start)
                                 if e_start.strftime("%H:%M") == time_str:
                                    self.service.events().delete(calendarId='primary', eventId=event['id']).execute()
                                    return True, "Slot unblocked"
                             except:
                                 continue
                return False, "Slot was not blocked"
                
        except Exception as e:
            return False, str(e)

    def book_slot(self, start_time_iso, duration_minutes=30, summary="Medical Appointment", description=""):
        if not self.service: return False, "Service not init"
        try:
            # Handle start_time_iso. 
            # If it comes as '2024-11-20T10:00' (naive), we add 'Z' or local offset.
            
            # Fetch timezone
            calendar_info = self.service.calendars().get(calendarId='primary').execute()
            tz_name = calendar_info.get('timeZone', 'UTC')
            tz = pytz.timezone(tz_name)

            # Check if iso string already has key
            valid_iso = start_time_iso
            
            # If naive (no + or Z), localize attempts
            if '+' not in start_time_iso and 'Z' not in start_time_iso:
                dt = datetime.datetime.fromisoformat(start_time_iso)
                dt = tz.localize(dt)
                valid_iso = dt.isoformat()

            start = datetime.datetime.fromisoformat(valid_iso)
            end = start + datetime.timedelta(minutes=duration_minutes)
            
            event = {
                'summary': summary,
                'description': description,
                'start': {'dateTime': start.isoformat()},
                'end': {'dateTime': end.isoformat()},
            }
            event = self.service.events().insert(calendarId='primary', body=event).execute()
            return True, event.get('htmlLink')
        except Exception as e:
            return False, str(e)
