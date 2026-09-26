import uuid
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base
from pgvector.sqlalchemy import Vector

Base = declarative_base()


class CallLog(Base):
    __tablename__ = "call_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    call_sid = Column(String(100), unique=True, nullable=False)
    caller_phone = Column(String(30))
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True))
    transcript = Column(Text)
    summary = Column(Text)


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cal_booking_id = Column(String(100))
    customer_name = Column(String(255))
    customer_email = Column(String(255))
    customer_phone = Column(String(30))
    slot_time = Column(DateTime(timezone=True), nullable=False)
    status = Column(String(50), default="confirmed")
    # Verification fields — required before ANY tool can modify/reveal this
    # appointment over a phone call, since caller ID alone isn't trustworthy
    # (unlike WhatsApp, where the sender number itself was a solid identity anchor).
    verification_code = Column(String(20))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class BusinessKnowledge(Base):
    __tablename__ = "business_knowledge"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category = Column(String(100))  # 'directions', 'doctors', 'pricing', etc.
    content = Column(Text, nullable=False)
    embedding = Column(Vector(1536))


class Staff(Base):
    """
    Routing table for transfer_to_staff — the doc's architecture had no
    concept of WHO an escalation actually goes to. Without this, the
    equivalent of escalate_to_human has nowhere real to send the caller.
    """
    __tablename__ = "staff"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    department = Column(String(100), nullable=False)  # 'Billing', 'Cardiology', etc.
    name = Column(String(255))
    phone_number = Column(String(30), nullable=False)  # where to transfer the live call
    notify_email = Column(String(255))  # for take_department_message
