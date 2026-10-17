import json
import os
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

KB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "knowledge_base", "clinic_faq.json")


def load_knowledge_base() -> Dict[str, Any]:
    """Loads the clinic FAQ and knowledge base JSON file."""
    if not os.path.exists(KB_PATH):
        logger.warning("Knowledge base JSON file not found at: %s", KB_PATH)
        return {}
    try:
        with open(KB_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error("Failed to load knowledge base file: %s", e)
        return {}


def query_pinecone_vector_db(query: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """
    Queries Pinecone vector database using OpenAI Embeddings if configured.
    Returns list of matching document snippets.
    """
    pinecone_key = os.environ.get("PINECONE_API_KEY")
    index_name = os.environ.get("PINECONE_INDEX_NAME", "dentnexa-kb")
    openai_key = os.environ.get("OPENAI_API_KEY")

    if not pinecone_key or not openai_key:
        logger.debug("Pinecone or OpenAI key missing. Skipping Pinecone vector query.")
        return []

    try:
        import pinecone
        from openai import OpenAI

        # Generate embedding vector for query
        client = OpenAI(api_key=openai_key)
        emb_res = client.embeddings.create(
            input=[query],
            model=os.environ.get("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
        )
        query_vector = emb_res.data[0].embedding

        # Query Pinecone
        pc = pinecone.Pinecone(api_key=pinecone_key)
        index = pc.Index(index_name)
        res = index.query(vector=query_vector, top_k=top_k, include_metadata=True)

        results = []
        for match in res.get("matches", []):
            metadata = match.get("metadata", {})
            results.append({
                "score": match.get("score", 0.0),
                "title": metadata.get("title", ""),
                "content": metadata.get("text", "")
            })
        return results

    except Exception as e:
        logger.warning("Pinecone query execution error: %s", e)
        return []


def search_knowledge_base(query: str) -> Dict[str, Any]:
    """
    Main RAG search entry point.
    First attempts Pinecone vector search, then complements with structured KB matcher.
    """
    logger.info("RAG search query: %s", query)
    
    # 1. Try Pinecone Vector Search
    pinecone_matches = query_pinecone_vector_db(query)
    if pinecone_matches:
        return {
            "source": "pinecone_vector_db",
            "matches": pinecone_matches
        }

    # 2. Structured Knowledge Base Search (Fallback/Local Matcher)
    kb = load_knowledge_base()
    query_lower = query.lower()
    matched_sections = []

    # Check Services & Prices
    for s in kb.get("services_and_prices", []):
        if any(w in query_lower for w in s["service"].lower().split()) or any(w in s["service"].lower() for w in query_lower.split()):
            matched_sections.append({
                "type": "service_price",
                "service": s["service"],
                "price": s["price_range"],
                "description": s["description"]
            })

    # Check Medical Instructions
    for inst in kb.get("medical_instructions", []):
        if any(w in query_lower for w in inst["topic"].lower().split()) or any(w in inst["topic"].lower() for w in query_lower.split()):
            matched_sections.append({
                "type": "medical_instruction",
                "topic": inst["topic"],
                "instructions": inst["instructions"]
            })

    # Check Clinic Info (Insurance, Working hours, Address)
    clinic_info = kb.get("clinic_info", {})
    if any(k in query_lower for k in ["تأمين", "امين", "insurance", "شركة"]):
        matched_sections.append({
            "type": "insurance",
            "accepted_insurances": clinic_info.get("accepted_insurances", [])
        })

    if any(k in query_lower for k in ["مواعيد", "ساعات", "دوام", "العنوان", "موقع", "طوارئ", "address", "hours"]):
        matched_sections.append({
            "type": "clinic_details",
            "name": clinic_info.get("name"),
            "working_hours": clinic_info.get("working_hours"),
            "address": clinic_info.get("address"),
            "emergency_phone": clinic_info.get("emergency_phone")
        })

    if not matched_sections:
        # Return default general clinic overview if no specific section matched
        matched_sections.append({
            "type": "general_info",
            "clinic_info": clinic_info,
            "services_summary": [s["service"] for s in kb.get("services_and_prices", [])]
        })

    return {
        "source": "structured_knowledge_base",
        "matches": matched_sections
    }
