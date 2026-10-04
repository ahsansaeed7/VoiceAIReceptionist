"""
query_knowledge_base tool — pgvector semantic search over business_knowledge.

Same embedding model as seed.py (text-embedding-3-small) so the query
vector and stored vectors live in the same space.
"""

from openai import OpenAI

from app.config import OPENAI_API_KEY
from app.db.session import SessionLocal
from app.db.models import BusinessKnowledge

client = OpenAI(api_key=OPENAI_API_KEY)


def _embed(text: str) -> list[float]:
    response = client.embeddings.create(model="text-embedding-3-small", input=text)
    return response.data[0].embedding


def query_knowledge_base(query: str, top_k: int = 2) -> dict:
    """
    Searches business facts (directions, hours, doctors, pricing) by
    semantic similarity. Returns the top_k most relevant entries.
    """
    query_vector = _embed(query)

    db = SessionLocal()
    try:
        # pgvector's <=> operator computes cosine distance — smaller is
        # more similar. order by it ascending, take the closest matches.
        results = (
            db.query(BusinessKnowledge)
            .order_by(BusinessKnowledge.embedding.cosine_distance(query_vector))
            .limit(top_k)
            .all()
        )

        return {
            "query": query,
            "results": [{"category": r.category, "content": r.content} for r in results],
        }
    finally:
        db.close()


QUERY_KNOWLEDGE_BASE_SCHEMA = {
    "type": "function",
    "name": "query_knowledge_base",
    "description": "Searches business facts including address, directions, parking, operating hours, available doctors, and pricing.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search prompt, e.g. 'where are you located' or 'what are your hours'.",
            },
        },
        "required": ["query"],
        "additionalProperties": False,
    },
}


if __name__ == "__main__":
    # Quick manual test — run with: python -m app.agent.tools.knowledge_base
    import json

    print("Query: 'where is your office'")
    print(json.dumps(query_knowledge_base("where is your office"), indent=2))

    print("\nQuery: 'how much does a visit cost'")
    print(json.dumps(query_knowledge_base("how much does a visit cost"), indent=2))