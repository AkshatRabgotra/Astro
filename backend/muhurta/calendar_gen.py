"""Calendar synchronization payload generator for Auspicious Muhurtas.

Produces:
1. RFC 5545 iCalendar (.ics) string for Apple Calendar, Outlook, and native devices.
2. 1-Click Google Calendar deep link URL.
"""

from datetime import datetime
import urllib.parse
from uuid import uuid4
from zoneinfo import ZoneInfo
from backend.muhurta.models import CalendarPayload


def generate_calendar_payload(
    title: str,
    description: str,
    location_name: str,
    start_dt: datetime,
    end_dt: datetime,
) -> CalendarPayload:
    """Generate RFC 5545 .ics content and 1-click Google Calendar URL."""
    # Format datetimes in UTC for standard calendar interop
    start_utc = start_dt.astimezone(ZoneInfo("UTC"))
    end_utc = end_dt.astimezone(ZoneInfo("UTC"))

    dtstart_str = start_utc.strftime("%Y%m%dT%H%M%SZ")
    dtend_str = end_utc.strftime("%Y%m%dT%H%M%SZ")
    dtstamp_str = datetime.now(ZoneInfo("UTC")).strftime("%Y%m%dT%H%M%SZ")
    uid_str = f"muhurta-{uuid4()}@melooha.ai"

    # Clean description for ICS (escape newlines and commas)
    clean_desc = description.replace("\n", "\\n").replace(",", "\\,")

    ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Melooha AI//Vedic Auspicious Muhurta Engine//EN
CALSCALE:GREGORIAN
METHOD:PUBLISH
BEGIN:VEVENT
UID:{uid_str}
DTSTAMP:{dtstamp_str}
DTSTART:{dtstart_str}
DTEND:{dtend_str}
SUMMARY:{title}
DESCRIPTION:{clean_desc}
LOCATION:{location_name}
STATUS:CONFIRMED
TRANSP:OPAQUE
BEGIN:VALARM
TRIGGER:-PT24H
ACTION:DISPLAY
DESCRIPTION:Reminder: Auspicious Muhurta window starts in 24 hours
END:VALARM
BEGIN:VALARM
TRIGGER:-PT1H
ACTION:DISPLAY
DESCRIPTION:Urgent: Auspicious Muhurta window starts in 1 hour
END:VALARM
END:VEVENT
END:VCALENDAR"""

    # Google Calendar Web URL
    params = {
        "action": "TEMPLATE",
        "text": title,
        "details": description,
        "location": location_name,
        "dates": f"{dtstart_str}/{dtend_str}",
    }
    google_url = f"https://calendar.google.com/calendar/render?{urllib.parse.urlencode(params)}"

    return CalendarPayload(
        title=title,
        description=description,
        location=location_name,
        start_time_iso=start_dt.isoformat(),
        end_time_iso=end_dt.isoformat(),
        google_calendar_url=google_url,
        ics_data=ics_content,
    )
