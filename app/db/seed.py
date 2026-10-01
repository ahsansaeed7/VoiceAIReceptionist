"""
Seed script — populates staff (for transfer_to_staff routing) and
business_knowledge (with real embeddings, for query_knowledge_base's
pgvector semantic search) so the tools have real data to work against.

Run with:
    python -m app.db.seed
"""

import os
from openai import OpenAI

from app.db.session import SessionLocal
from app.db.models import Staff, BusinessKnowledge

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

STAFF = [
    {"department": "Front Desk", "name": "Reception", "phone_number": "+10000000001", "notify_email": "frontdesk@example.com"},
    {"department": "Billing", "name": "Billing Team", "phone_number": "+10000000002", "notify_email": "billing@example.com"},
    {"department": "Cardiology", "name": "Dr. Smith", "phone_number": "+10000000003", "notify_email": "cardiology@example.com"},
]

KNOWLEDGE = [
    {"category": "directions", "content": "We're located at 123 Main Street, Suite 200. Parking is available in the lot behind the building, free for patients."},
    {"category": "hours", "content": "We're open Monday to Friday, 9am to 5pm. Closed on weekends and public holidays."},
    {"category": "doctors", "content": "Dr. Smith (Cardiology) is available Monday, Wednesday, and Friday. Dr. Lee (General Practice) is available Tuesday and Thursday."},
    {"category": "pricing", "content": "A standard consultation is $75. Specialist consultations start at $150. We accept most major insurance plans."},
]


def embed(text: str) -> list[float]:
    response = client.embeddings.create(model="text-embedding-3-small", input=text)
    return response.data[0].embedding


def seed():
    db = SessionLocal()
    try:
        for s in STAFF:
            existing = db.query(Staff).filter_by(department=s["department"]).first()
            if existing:
                print(f"Skipping (exists): {s['department']} staff")
                continue
            db.add(Staff(**s))
            print(f"Added staff: {s['department']}")

        for k in KNOWLEDGE:
            existing = db.query(BusinessKnowledge).filter_by(category=k["category"]).first()
            if existing:
                print(f"Skipping (exists): {k['category']} knowledge")
                continue
            entry = BusinessKnowledge(
                category=k["category"],
                content=k["content"],
                embedding=embed(k["content"]),
            )
            db.add(entry)
            print(f"Added knowledge: {k['category']}")

        db.commit()
        print("Seeding complete.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
