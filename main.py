import os
import uuid
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Depends, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from dotenv import load_dotenv

load_dotenv()

from backend.database.session import init_db, get_db
from backend.models.schemas import (
    EnvironmentalData,
    AssessmentResponse,
    ChatRequest,
    ChatResponse,
    EnvironmentalProfileCreate,
    EnvironmentalProfileResponse,
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
    KnowledgeSearchResultItem,
    DocumentIngestRequest,
    Recommendation,
    ScenarioPreset
)
from backend.models.db_models import (
    Conversation,
    Message,
    EnvironmentalProfile,
    EnvironmentalMetricsRecord,
    KnowledgeDocumentRecord,
    KnowledgeChunkRecord,
    RecommendationRecord,
    EvidenceSourceRecord
)
from backend.rag.reasoning import get_assessment
from backend.rag.vectorstore import retriever
from backend.services.conversation_manager import conversation_manager
from backend.recommendations.generator import recommendation_engine
from backend.reasoning.engine import reasoning_engine
from backend.utils.metric_helpers import evaluate_health_overview, calculate_data_completeness

# Initialize database schema
init_db()

app = FastAPI(
    title="Darukaa.Earth - AI Biodiversity Intelligence API",
    description="Scientific environmental intelligence system providing multi-metric reasoning and evidence-backed recommendations.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {
        "system": "Darukaa.Earth AI Biodiversity Intelligence Platform",
        "status": "operational",
        "knowledge_documents_indexed": retriever.count(),
        "version": "1.0.0"
    }

# 1. POST /api/chat - Multi-turn conversational intelligence
@app.post("/api/chat", response_model=ChatResponse)
@app.post("/chat", response_model=ChatResponse) # legacy compatibility
def chat_endpoint(request: ChatRequest, db: Session = Depends(get_db)):
    conv_id, accumulated_context, requires_more_info, missing_fields, reply_text = conversation_manager.process_turn(
        db=db,
        conversation_id=request.conversation_id,
        user_message=request.message,
        incoming_context=request.context
    )

    assessment = None
    # If we have enough data (at least 3 environmental variables), run RAG reasoning
    if not requires_more_info:
        assessment = get_assessment(accumulated_context)
        reply_text = (
            f"**ECOLOGICAL ASSESSMENT COMPLETE**\n\n"
            f"{assessment.assessment}\n\n"
            f"**Key Environmental Drivers Identified:**\n"
            + "\n".join([f"- {d}" for d in assessment.key_environmental_drivers])
            + f"\n\n**Multi-Metric Scientific Reasoning:**\n{assessment.multi_metric_reasoning}"
        )

        # Update the assistant message in DB with full content
        latest_asst_msg = db.query(Message).filter_by(
            conversation_id=conv_id,
            role="assistant"
        ).order_by(Message.created_at.desc()).first()
        if latest_asst_msg:
            latest_asst_msg.content = reply_text
            db.commit()

    return ChatResponse(
        conversation_id=conv_id,
        message=reply_text,
        requires_more_info=requires_more_info,
        missing_fields=missing_fields if requires_more_info else [],
        extracted_context=accumulated_context,
        assessment=assessment
    )

# 2. POST /api/analyze - Direct multi-metric analysis
@app.post("/api/analyze", response_model=AssessmentResponse)
@app.post("/assessment", response_model=AssessmentResponse) # legacy compatibility
def analyze_endpoint(data: EnvironmentalData, db: Session = Depends(get_db)):
    assessment = get_assessment(data)
    return assessment

# 3. POST /api/recommendations - Direct recommendation generation
@app.post("/api/recommendations", response_model=List[Recommendation])
def recommendations_endpoint(data: EnvironmentalData):
    assessment = get_assessment(data)
    return assessment.recommendations

# 4. POST /api/environmental-profile - Create or update profile
@app.post("/api/environmental-profile", response_model=EnvironmentalProfileResponse)
def create_profile(profile_in: EnvironmentalProfileCreate, db: Session = Depends(get_db)):
    profile = EnvironmentalProfile(
        id=str(uuid.uuid4()),
        conversation_id=profile_in.conversation_id,
        name=profile_in.name,
        region=profile_in.region or profile_in.metrics.region,
        latitude=profile_in.latitude or profile_in.metrics.latitude,
        longitude=profile_in.longitude or profile_in.metrics.longitude,
        climate_zone=profile_in.climate_zone
    )
    db.add(profile)
    db.flush()

    m = profile_in.metrics
    metrics_rec = EnvironmentalMetricsRecord(
        profile_id=profile.id,
        soil_ph=m.soil.ph if m.soil else None,
        soil_organic_carbon=m.soil.organic_carbon if m.soil else None,
        soil_moisture=m.soil.moisture if m.soil else None,
        soil_fertility=m.soil.fertility if m.soil else None,
        soil_degradation_indicators=m.soil.degradation_indicators if m.soil else None,
        temperature=m.climate.temperature if m.climate else None,
        rainfall=m.climate.rainfall if m.climate else None,
        rainfall_amount_mm=m.climate.rainfall_amount_mm if m.climate else None,
        rainfall_pattern=m.climate.rainfall_pattern if m.climate else None,
        drought_conditions=m.climate.drought_conditions if m.climate else None,
        land_use=m.land.land_use if m.land else None,
        crop=m.land.crop if m.land else None,
        habitat_fragmentation=m.land.habitat_fragmentation if m.land else None,
        species_richness=m.biodiversity.species_richness if m.biodiversity else None,
        habitat_diversity=m.biodiversity.habitat_diversity if m.biodiversity else None,
        pollinator_diversity=m.biodiversity.pollinator_diversity if m.biodiversity else None,
        microbial_diversity=m.biodiversity.microbial_diversity if m.biodiversity else None,
        pollution=m.human_impact.pollution if m.human_impact else None,
        deforestation=m.human_impact.deforestation if m.human_impact else None,
        agricultural_intensity=m.human_impact.agricultural_intensity if m.human_impact else None
    )
    db.add(metrics_rec)
    db.commit()

    return EnvironmentalProfileResponse(
        id=profile.id,
        name=profile.name,
        region=profile.region,
        latitude=profile.latitude,
        longitude=profile.longitude,
        climate_zone=profile.climate_zone,
        metrics=profile_in.metrics,
        created_at=profile.created_at.isoformat()
    )

# 5. GET /api/metrics/:profileId - Retrieve metrics and health overview
@app.get("/api/metrics/{profile_id}")
def get_profile_metrics(profile_id: str, db: Session = Depends(get_db)):
    profile = db.query(EnvironmentalProfile).filter_by(id=profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    m_rec = profile.metrics
    data = EnvironmentalData(
        region=profile.region,
        latitude=profile.latitude,
        longitude=profile.longitude,
        soil={
            "ph": m_rec.soil_ph if m_rec else None,
            "organic_carbon": m_rec.soil_organic_carbon if m_rec else None,
            "moisture": m_rec.soil_moisture if m_rec else None,
            "fertility": m_rec.soil_fertility if m_rec else None,
            "degradation_indicators": m_rec.soil_degradation_indicators if m_rec else None
        },
        climate={
            "rainfall": m_rec.rainfall if m_rec else None,
            "rainfall_amount_mm": m_rec.rainfall_amount_mm if m_rec else None,
            "rainfall_pattern": m_rec.rainfall_pattern if m_rec else None,
            "temperature": m_rec.temperature if m_rec else None,
            "drought_conditions": m_rec.drought_conditions if m_rec else None
        },
        land={
            "land_use": m_rec.land_use if m_rec else None,
            "crop": m_rec.crop if m_rec else None,
            "habitat_fragmentation": m_rec.habitat_fragmentation if m_rec else None
        },
        biodiversity={
            "species_richness": m_rec.species_richness if m_rec else None,
            "habitat_diversity": m_rec.habitat_diversity if m_rec else None,
            "pollinator_diversity": m_rec.pollinator_diversity if m_rec else None,
            "microbial_diversity": m_rec.microbial_diversity if m_rec else None
        },
        human_impact={
            "pollution": m_rec.pollution if m_rec else None,
            "deforestation": m_rec.deforestation if m_rec else None,
            "agricultural_intensity": m_rec.agricultural_intensity if m_rec else None
        }
    )

    health_overview = evaluate_health_overview(data)
    completeness_pct, present, missing = calculate_data_completeness(data)

    return {
        "profile_id": profile.id,
        "name": profile.name,
        "region": profile.region,
        "metrics": data,
        "health_overview": health_overview,
        "completeness_pct": completeness_pct,
        "missing_metrics": missing
    }

# 6. POST /api/knowledge/search - Semantic vector search
@app.post("/api/knowledge/search", response_model=KnowledgeSearchResponse)
def search_knowledge(search_req: KnowledgeSearchRequest, db: Session = Depends(get_db)):
    results = retriever.search(search_req.query, n_results=search_req.limit or 5, category_filter=search_req.category)
    
    formatted_items = []
    for r in results:
        meta = r.get("metadata", {})
        formatted_items.append(KnowledgeSearchResultItem(
            document_id=meta.get("document_id", r.get("id", "doc_unknown")),
            title=meta.get("title", "Scientific Publication"),
            author_org=meta.get("author_org", "Scientific Organization"),
            citation=meta.get("citation", "Citation Unavailable"),
            snippet=r.get("text", "")[:350],
            relevance_score=r.get("relevance_score", 0.75),
            category=meta.get("category", "General")
        ))

    return KnowledgeSearchResponse(query=search_req.query, results=formatted_items)

# 7. GET /api/evidence/:id - Document details
@app.get("/api/evidence/{doc_id}")
def get_evidence_detail(doc_id: str, db: Session = Depends(get_db)):
    doc = db.query(KnowledgeDocumentRecord).filter_by(id=doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Evidence document not found")

    return {
        "id": doc.id,
        "title": doc.title,
        "author_org": doc.author_org,
        "citation": doc.citation,
        "publication_year": doc.publication_year,
        "category": doc.category,
        "doi_url": doc.doi_url,
        "summary": doc.summary,
        "full_text": doc.full_text,
        "chunks_count": len(doc.chunks)
    }

# 8. POST /api/knowledge/ingest - Dynamic document ingestion
@app.post("/api/knowledge/ingest")
def ingest_document(ingest_req: DocumentIngestRequest, db: Session = Depends(get_db)):
    doc_id = f"doc_{uuid.uuid4().hex[:8]}"
    doc = KnowledgeDocumentRecord(
        id=doc_id,
        title=ingest_req.title,
        author_org=ingest_req.author_org,
        citation=ingest_req.citation,
        publication_year=ingest_req.publication_year,
        category=ingest_req.category,
        summary=ingest_req.summary or ingest_req.content[:300],
        full_text=ingest_req.content
    )
    db.add(doc)
    db.commit()

    # Chunk and embed
    paragraphs = [p.strip() for p in ingest_req.content.split("\n\n") if p.strip()]
    texts = []
    metas = []
    ids = []
    for idx, p in enumerate(paragraphs):
        c_id = f"{doc_id}_chk_{idx}"
        chunk_rec = KnowledgeChunkRecord(
            id=c_id,
            document_id=doc.id,
            chunk_index=idx,
            text=p,
            topic=ingest_req.category,
            embedding_id=c_id
        )
        db.add(chunk_rec)
        texts.append(p)
        metas.append({
            "document_id": doc.id,
            "title": doc.title,
            "author_org": doc.author_org,
            "citation": doc.citation,
            "category": doc.category,
            "chunk_index": idx
        })
        ids.append(c_id)

    db.commit()
    retriever.add_documents(texts, metas, ids)

    return {"message": "Document successfully ingested and indexed in ChromaDB", "document_id": doc.id, "chunks": len(texts)}

# 9. GET /api/conversations - List conversations
@app.get("/api/conversations")
def list_conversations(limit: int = 15, db: Session = Depends(get_db)):
    convs = db.query(Conversation).order_by(Conversation.updated_at.desc()).limit(limit).all()
    return [
        {
            "id": c.id,
            "title": c.title,
            "created_at": c.created_at.isoformat(),
            "updated_at": c.updated_at.isoformat(),
            "message_count": len(c.messages)
        }
        for c in convs
    ]

# 10. GET /api/conversations/:id - Get conversation history
@app.get("/api/conversations/{conversation_id}")
def get_conversation(conversation_id: str, db: Session = Depends(get_db)):
    conv = db.query(Conversation).filter_by(id=conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = [
        {
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "requires_more_info": bool(m.requires_more_info),
            "extracted_context": m.extracted_context_json,
            "created_at": m.created_at.isoformat()
        }
        for m in conv.messages
    ]

    latest_context = None
    for m in reversed(conv.messages):
        if m.extracted_context_json:
            latest_context = m.extracted_context_json
            break

    return {
        "id": conv.id,
        "title": conv.title,
        "created_at": conv.created_at.isoformat(),
        "messages": messages,
        "latest_context": latest_context
    }

# 11. GET /api/scenarios - Pre-seeded hackathon scenarios
@app.get("/api/scenarios")
def get_scenarios(db: Session = Depends(get_db)):
    from knowledge_base.seed import SCENARIO_SEEDS
    
    scenarios = []
    for s in SCENARIO_SEEDS:
        m = s["metrics"]
        data = EnvironmentalData(
            region=s["region"],
            latitude=s["latitude"],
            longitude=s["longitude"],
            soil={
                "ph": m.get("soil_ph"),
                "organic_carbon": m.get("soil_organic_carbon"),
                "moisture": m.get("soil_moisture"),
                "fertility": m.get("soil_fertility"),
                "degradation_indicators": m.get("soil_degradation_indicators")
            },
            climate={
                "rainfall": m.get("rainfall"),
                "rainfall_amount_mm": m.get("rainfall_amount_mm"),
                "rainfall_pattern": m.get("rainfall_pattern"),
                "temperature": m.get("temperature"),
                "drought_conditions": m.get("drought_conditions")
            },
            land={
                "land_use": m.get("land_use"),
                "crop": m.get("crop"),
                "habitat_fragmentation": m.get("habitat_fragmentation")
            },
            biodiversity={
                "species_richness": m.get("species_richness"),
                "habitat_diversity": m.get("habitat_diversity"),
                "pollinator_diversity": m.get("pollinator_diversity"),
                "microbial_diversity": m.get("microbial_diversity")
            },
            human_impact={
                "pollution": m.get("pollution"),
                "deforestation": m.get("deforestation"),
                "agricultural_intensity": m.get("agricultural_intensity")
            }
        )

        scenarios.append({
            "id": s["id"],
            "title": s["name"],
            "subtitle": f"{s['region']} | {m.get('crop')} | SOC: {m.get('soil_organic_carbon')}%",
            "description": f"Target scenario addressing {m.get('soil_degradation_indicators') or 'biodiversity stress'} under {m.get('rainfall')} rainfall.",
            "data": data,
            "focus_areas": [
                "Multi-metric soil-climate interaction",
                "Non-obvious agroforestry / corridor recommendation",
                "FAO / IPCC evidence linking"
            ]
        })

    return scenarios

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.api.main:app", host="0.0.0.0", port=8000, reload=True)
