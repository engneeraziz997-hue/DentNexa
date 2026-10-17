import os
import json
import logging

logger = logging.getLogger(__name__)


def ingest_knowledge_base_to_pinecone():
    """
    Ingests clinic FAQ knowledge base JSON documents into Pinecone Vector Database
    using OpenAI Embeddings text-embedding-3-small.
    """
    pinecone_key = os.environ.get("PINECONE_API_KEY")
    index_name = os.environ.get("PINECONE_INDEX_NAME", "dentnexa-kb")
    openai_key = os.environ.get("OPENAI_API_KEY")

    if not pinecone_key or not openai_key:
        print("❌ Error: PINECONE_API_KEY and OPENAI_API_KEY environment variables are required.")
        return

    kb_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "knowledge_base", "clinic_faq.json")
    if not os.path.exists(kb_path):
        print(f"❌ Error: Knowledge base file not found at {kb_path}")
        return

    with open(kb_path, "r", encoding="utf-8") as f:
        kb_data = json.load(f)

    documents = []
    
    # Process services & prices
    for idx, s in enumerate(kb_data.get("services_and_prices", [])):
        text = f"خدمة الأسنان: {s['service']}\nالسعر التقديري: {s['price_range']}\nالوصف: {s['description']}"
        documents.append({
            "id": f"service_{idx}",
            "title": s["service"],
            "text": text
        })

    # Process medical instructions
    for idx, inst in enumerate(kb_data.get("medical_instructions", [])):
        text = f"الموضوع الطبي: {inst['topic']}\nالتعليمات: {inst['instructions']}"
        documents.append({
            "id": f"medical_{idx}",
            "title": inst["topic"],
            "text": text
        })

    # Process clinic info
    clinic = kb_data.get("clinic_info", {})
    text = (
        f"عيادة الأسنان: {clinic.get('name')}\n"
        f"ساعات العمل: {clinic.get('working_hours')}\n"
        f"العنوان والموقع: {clinic.get('address')}\n"
        f"هاتف الطوارئ: {clinic.get('emergency_phone')}\n"
        f"شركات التأمين المقبولة: {', '.join(clinic.get('accepted_insurances', []))}"
    )
    documents.append({
        "id": "clinic_info_main",
        "title": "معلومات العيادة والتأمين",
        "text": text
    })

    print(f"📦 Preparing to ingest {len(documents)} documents into Pinecone index '{index_name}'...")

    try:
        import pinecone
        from openai import OpenAI

        openai_client = OpenAI(api_key=openai_key)
        pc = pinecone.Pinecone(api_key=pinecone_key)

        # Ensure index exists
        existing_indexes = [idx.name for idx in pc.list_indexes()]
        if index_name not in existing_indexes:
            print(f"🔨 Creating Pinecone index '{index_name}'...")
            pc.create_index(
                name=index_name,
                dimension=1536,
                metric="cosine",
                spec=pinecone.ServerlessSpec(cloud="aws", region="us-east-1")
            )

        index = pc.Index(index_name)
        vectors_to_upsert = []

        for doc in documents:
            emb_res = openai_client.embeddings.create(
                input=[doc["text"]],
                model="text-embedding-3-small"
            )
            vector = emb_res.data[0].embedding
            vectors_to_upsert.append({
                "id": doc["id"],
                "values": vector,
                "metadata": {"title": doc["title"], "text": doc["text"]}
            })

        index.upsert(vectors=vectors_to_upsert)
        print("✅ Knowledge Base successfully ingested into Pinecone Vector DB!")

    except Exception as e:
        print(f"❌ Error during Pinecone ingestion: {e}")


if __name__ == "__main__":
    ingest_knowledge_base_to_pinecone()
