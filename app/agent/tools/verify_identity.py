"""
verify_caller_identity tool — required before revealing or modifying ANY
existing appointment. Caller ID over a phone line is not a trustworthy
identity anchor (unlike WhatsApp's sender number), so anything touching an
existing booking must be gated behind this.
"""

from app.db.session import SessionLocal
from app.db.models import Appointment


def verify_caller_identity(phone_or_email: str, verification_code: str) -> dict:
    db = SessionLocal()
    try:
        appt = (
            db.query(Appointment)
            .filter(
                (Appointment.customer_phone == phone_or_email) | (Appointment.customer_email == phone_or_email),
                Appointment.verification_code == verification_code,
            )
            .first()
        )
        if appt is None:
            return {"verified": False}

        return {
            "verified": True,
            "appointment_id": str(appt.id),
            "customer_name": appt.customer_name,
            "slot_time": str(appt.slot_time),
            "status": appt.status,
        }
    finally:
        db.close()


VERIFY_CALLER_IDENTITY_SCHEMA = {
    "type": "function",
    "name": "verify_caller_identity",
    "description": "Verifies a caller's identity before discussing or changing an EXISTING appointment. Always call this first if the caller references a booking they already have — never take their word for who they are.",
    "parameters": {
        "type": "object",
        "properties": {
            "phone_or_email": {"type": "string", "description": "Phone number or email the caller provides."},
            "verification_code": {"type": "string", "description": "Confirmation code from their booking."},
        },
        "required": ["phone_or_email", "verification_code"],
        "additionalProperties": False,
    },
}