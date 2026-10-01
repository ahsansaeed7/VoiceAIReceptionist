"""
Cal.com-backed scheduling tools.

Plain, standalone-testable functions — no Realtime API involved yet.
book_appointment combines booking + local DB record + notification trigger
into one call (same "guarantee the side effect" pattern as the WhatsApp
project's approve_booking), so the model never has to remember a separate
notify step.
"""

import httpx

from app.config import CALCOM_API_KEY, CALCOM_EVENT_TYPE_ID
from app.db.session import SessionLocal
from app.db.models import Appointment

CAL_BASE_URL = "https://api.cal.com/v2"

# IMPORTANT: Cal.com versions each endpoint independently via cal-api-version,
# and these values DO change over time (confirmed: bookings moved from
# 2024-08-13 to 2026-02-25). Never assume one shared version works everywhere
# — check https://cal.com/docs/api-reference/v2/<endpoint> for the current
# required value if either of these ever starts returning errors.
SLOTS_API_VERSION = "2024-09-04"
BOOKINGS_API_VERSION = "2026-02-25"


def _headers(api_version: str) -> dict:
    return {
        "Authorization": f"Bearer {CALCOM_API_KEY}",
        "Content-Type": "application/json",
        "cal-api-version": api_version,
    }


def check_available_slots(date: str, event_type_id: str = None) -> dict:
    """
    Checks available booking slots from Cal.com for a given date.
    date: YYYY-MM-DD. Queries the full day, midnight to midnight UTC.
    """
    event_type_id = event_type_id or CALCOM_EVENT_TYPE_ID
    start_time = f"{date}T00:00:00Z"
    end_time = f"{date}T23:59:59Z"

    # NOTE: this endpoint version (2024-09-04) requires "start"/"end" as the
    # param names, NOT "startTime"/"endTime" — confirmed via the actual
    # BadRequestException response, since docs examples elsewhere show the
    # older param names for a different api-version.
    params = {
        "eventTypeId": event_type_id,
        "start": start_time,
        "end": end_time,
    }

    response = httpx.get(f"{CAL_BASE_URL}/slots", headers=_headers(SLOTS_API_VERSION), params=params, timeout=10)
    response.raise_for_status()
    data = response.json()

    # Flatten Cal.com's response into a simple list of ISO start times
    slots = []
    for day_slots in data.get("data", {}).values():
        for slot in day_slots:
            slots.append(slot.get("start"))

    return {"date": date, "available_slots": slots}


def book_appointment(name: str, email: str, start_time: str, phone: str = None, event_type_id: str = None) -> dict:
    """
    Books a slot in Cal.com, then mirrors it into our local appointments
    table (for the staff dashboard + identity verification lookups later).
    Does NOT send the confirmation itself yet — that's wired in once
    notifications.py exists, same pattern as the WhatsApp project's
    approve_booking triggering send_text as part of the same action.
    """
    event_type_id = event_type_id or CALCOM_EVENT_TYPE_ID

    payload = {
        "eventTypeId": int(event_type_id),
        "start": start_time,
        "attendee": {
            "name": name,
            "email": email,
            "timeZone": "UTC",
        },
    }

    response = httpx.post(f"{CAL_BASE_URL}/bookings", headers=_headers(BOOKINGS_API_VERSION), json=payload, timeout=10)

    if response.status_code >= 400:
        return {"error": f"Cal.com booking failed: {response.status_code} {response.text}"}

    cal_data = response.json().get("data", {})
    cal_booking_id = str(cal_data.get("uid", ""))

    db = SessionLocal()
    try:
        appt = Appointment(
            cal_booking_id=cal_booking_id,
            customer_name=name,
            customer_email=email,
            customer_phone=phone,
            slot_time=start_time,
            status="confirmed",
        )
        db.add(appt)
        db.commit()
        return {
            "appointment_id": str(appt.id),
            "cal_booking_id": cal_booking_id,
            "start_time": start_time,
            "status": "confirmed",
        }
    except Exception as e:
        db.rollback()
        return {"error": f"Booked in Cal.com but failed to save locally: {e}"}
    finally:
        db.close()


# Flat schema format — this is what OpenAI's Realtime API expects directly
# in its session tool list (different from Chat Completions' nested
# {"type":"function","function":{...}} wrapper used for Groq earlier).
CHECK_AVAILABLE_SLOTS_SCHEMA = {
    "type": "function",
    "name": "check_available_slots",
    "description": "Checks available booking slots from Cal.com for a given date.",
    "parameters": {
        "type": "object",
        "properties": {
            "date": {"type": "string", "description": "Date to query, YYYY-MM-DD format."},
            "event_type_id": {"type": ["string", "null"], "description": "Optional specific event type ID."},
        },
        "required": ["date", "event_type_id"],
        "additionalProperties": False,
    },
}

BOOK_APPOINTMENT_SCHEMA = {
    "type": "function",
    "name": "book_appointment",
    "description": "Books a confirmed slot in Cal.com for the caller. Only call this once the caller has confirmed a specific available time.",
    "parameters": {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Full name of the caller."},
            "email": {"type": "string", "description": "Caller's email address for confirmation."},
            "start_time": {"type": "string", "description": "ISO 8601 start time of the chosen slot."},
            "phone": {"type": ["string", "null"], "description": "Caller's phone number, if provided."},
            "event_type_id": {"type": ["string", "null"], "description": "Optional specific event type ID."},
        },
        "required": ["name", "email", "start_time", "phone", "event_type_id"],
        "additionalProperties": False,
    },
}


if __name__ == "__main__":
    # Quick manual test — run with: python -m app.agent.tools.scheduling
    import json
    from datetime import date, timedelta

    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    print(f"Checking slots for {tomorrow}:")
    print(json.dumps(check_available_slots(tomorrow), indent=2))