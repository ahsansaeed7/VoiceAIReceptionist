"""
take_department_message tool — relays a caller's message to the right
department, since the agent can't resolve everything itself.
"""

from app.db.session import SessionLocal
from app.db.models import Staff
from app.workers.notifications import send_email


def take_department_message(department: str, caller_name: str, message_content: str, caller_phone: str = None) -> dict:
    db = SessionLocal()
    try:
        staff = db.query(Staff).filter(Staff.department.ilike(department)).first()
        if staff is None:
            return {"error": f"No department found matching '{department}'."}

        if staff.notify_email:
            send_email(
                to=staff.notify_email,
                subject=f"Message from {caller_name} via Voice Receptionist",
                body=f"Caller: {caller_name}\nPhone: {caller_phone or 'not provided'}\n\nMessage:\n{message_content}",
            )

        return {"delivered_to": department, "staff_name": staff.name}
    finally:
        db.close()


TAKE_DEPARTMENT_MESSAGE_SCHEMA = {
    "type": "function",
    "name": "take_department_message",
    "description": "Takes a message from the caller and notifies the specified department by email.",
    "parameters": {
        "type": "object",
        "properties": {
            "department": {"type": "string", "description": "Target department, e.g. Billing, Cardiology, Front Desk."},
            "caller_name": {"type": "string"},
            "caller_phone": {"type": ["string", "null"]},
            "message_content": {"type": "string", "description": "Detailed summary of the caller's message."},
        },
        "required": ["department", "caller_name", "caller_phone", "message_content"],
        "additionalProperties": False,
    },
}