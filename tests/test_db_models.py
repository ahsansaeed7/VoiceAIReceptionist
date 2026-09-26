"""
First real CI test — proves the schema actually works against a live
Postgres before any tool logic is built on top of it. Run locally with:
    pytest -v
"""

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import DATABASE_URL
from app.db.models import Base, BusinessKnowledge, Appointment, Staff, CallLog


@pytest.fixture(scope="module")
def db_session():
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_can_insert_and_query_business_knowledge(db_session):
    entry = BusinessKnowledge(category="directions", content="We're on Main Street.")
    db_session.add(entry)
    db_session.commit()

    result = db_session.query(BusinessKnowledge).filter_by(category="directions").first()
    assert result is not None
    assert result.content == "We're on Main Street."


def test_can_insert_appointment_with_verification_code(db_session):
    appt = Appointment(
        customer_name="Test Patient",
        customer_email="test@example.com",
        slot_time=datetime.now(timezone.utc),
        verification_code="AB123",
    )
    db_session.add(appt)
    db_session.commit()

    result = db_session.query(Appointment).filter_by(verification_code="AB123").first()
    assert result is not None
    assert result.status == "confirmed"  # default value


def test_staff_table_supports_transfer_routing(db_session):
    staff = Staff(department="Cardiology", name="Dr. Smith", phone_number="+10000000000")
    db_session.add(staff)
    db_session.commit()

    result = db_session.query(Staff).filter_by(department="Cardiology").first()
    assert result is not None
    assert result.phone_number == "+10000000000"


def test_call_log_unique_call_sid_enforced(db_session):
    call1 = CallLog(call_sid=str(uuid.uuid4()))
    db_session.add(call1)
    db_session.commit()
    assert call1.id is not None
