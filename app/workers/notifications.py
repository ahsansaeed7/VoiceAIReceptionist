"""
Resend-backed email notifications — used by take_department_message and
later by booking confirmations.
"""

import resend
from app.config import RESEND_API_KEY

resend.api_key = RESEND_API_KEY


def send_email(to: str, subject: str, body: str) -> dict:
    try:
        result = resend.Emails.send({
            "from": "receptionist@yourdomain.com",  # must be a domain verified in your Resend account
            "to": [to],
            "subject": subject,
            "text": body,
        })
        return {"sent": True, "id": result.get("id")}
    except Exception as e:
        return {"sent": False, "error": str(e)}