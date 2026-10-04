"""
Tool registry — OpenAI Realtime flat schema format (different from Groq's
nested {"type":"function","function":{...}} wrapper used in the WhatsApp
project; Realtime wants the fields directly at the top level).
"""

from app.agent.tools.scheduling import (
    check_available_slots, CHECK_AVAILABLE_SLOTS_SCHEMA,
    book_appointment, BOOK_APPOINTMENT_SCHEMA,
)
from app.agent.tools.knowledge_base import query_knowledge_base, QUERY_KNOWLEDGE_BASE_SCHEMA
from app.agent.tools.messages import take_department_message, TAKE_DEPARTMENT_MESSAGE_SCHEMA
from app.agent.tools.verify_identity import verify_caller_identity, VERIFY_CALLER_IDENTITY_SCHEMA
from app.agent.tools.escalate import transfer_to_staff, TRANSFER_TO_STAFF_SCHEMA

TOOL_SCHEMAS = [
    CHECK_AVAILABLE_SLOTS_SCHEMA,
    BOOK_APPOINTMENT_SCHEMA,
    QUERY_KNOWLEDGE_BASE_SCHEMA,
    TAKE_DEPARTMENT_MESSAGE_SCHEMA,
    VERIFY_CALLER_IDENTITY_SCHEMA,
    TRANSFER_TO_STAFF_SCHEMA,
]

TOOL_FUNCTIONS = {
    "check_available_slots": check_available_slots,
    "book_appointment": book_appointment,
    "query_knowledge_base": query_knowledge_base,
    "take_department_message": take_department_message,
    "verify_caller_identity": verify_caller_identity,
    "transfer_to_staff": transfer_to_staff,
}