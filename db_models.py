import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Text, Integer, JSON
from sqlalchemy.orm import relationship
from backend.database.session import Base

def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid)
    username = Column(String(100), unique=True, nullable=False, default="demo_user")
    email = Column(String(255), unique=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    title = Column(String(255), default="Biodiversity Analysis")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")
    profiles = relationship("EnvironmentalProfile", back_populates="conversation", cascade="all, delete-orphan")
    recommendations = relationship("RecommendationRecord", back_populates="conversation", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=generate_uuid)
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False)
    role = Column(String(20), nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)
    requires_more_info = Column(Integer, default=0) # 0 or 1
    extracted_context_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")

class EnvironmentalProfile(Base):
    __tablename__ = "environmental_profiles"

    id = Column(String, primary_key=True, default=generate_uuid)
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=True)
    name = Column(String(255), default="Land Assessment Profile")
    region = Column(String(100), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    climate_zone = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="profiles")
    metrics = relationship("EnvironmentalMetricsRecord", back_populates="profile", uselist=False, cascade="all, delete-orphan")
    recommendations = relationship("RecommendationRecord", back_populates="profile", cascade="all, delete-orphan")

class EnvironmentalMetricsRecord(Base):
    __tablename__ = "environmental_metrics"

    id = Column(String, primary_key=True, default=generate_uuid)
    profile_id = Column(String, ForeignKey("environmental_profiles.id"), nullable=False, unique=True)
    
    # Soil Health
    soil_ph = Column(Float, nullable=True)
    soil_organic_carbon = Column(Float, nullable=True)
    soil_moisture = Column(Float, nullable=True)
    soil_fertility = Column(String(100), nullable=True)
    soil_degradation_indicators = Column(String(255), nullable=True)
    
    # Climate
    temperature = Column(Float, nullable=True)
    rainfall = Column(String(100), nullable=True)
    rainfall_amount_mm = Column(Float, nullable=True)
    rainfall_pattern = Column(String(100), nullable=True)
    drought_conditions = Column(String(100), nullable=True)
    
    # Land Use / Cover
    land_use = Column(String(100), nullable=True)
    crop = Column(String(100), nullable=True)
    habitat_fragmentation = Column(String(100), nullable=True)
    vegetation_cover = Column(String(100), nullable=True)
    
    # Biodiversity Indicators
    species_richness = Column(String(100), nullable=True)
    habitat_diversity = Column(String(100), nullable=True)
    pollinator_diversity = Column(String(100), nullable=True)
    microbial_diversity = Column(String(100), nullable=True)
    native_species_ratio = Column(Float, nullable=True)
    
    # Human Impact
    pollution = Column(String(100), nullable=True)
    deforestation = Column(String(100), nullable=True)
    agricultural_intensity = Column(String(100), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    profile = relationship("EnvironmentalProfile", back_populates="metrics")

class KnowledgeDocumentRecord(Base):
    __tablename__ = "knowledge_documents"

    id = Column(String, primary_key=True, default=generate_uuid)
    title = Column(String(255), nullable=False)
    author_org = Column(String(255), nullable=False) # e.g. FAO, IPCC, Nature
    citation = Column(Text, nullable=False)
    publication_year = Column(Integer, nullable=True)
    category = Column(String(100), nullable=True) # Soil, Biodiversity, Agroforestry, Climate, Restoration
    doi_url = Column(String(255), nullable=True)
    summary = Column(Text, nullable=True)
    full_text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    chunks = relationship("KnowledgeChunkRecord", back_populates="document", cascade="all, delete-orphan")
    evidence_sources = relationship("EvidenceSourceRecord", back_populates="document")

class KnowledgeChunkRecord(Base):
    __tablename__ = "knowledge_chunks"

    id = Column(String, primary_key=True, default=generate_uuid)
    document_id = Column(String, ForeignKey("knowledge_documents.id"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    topic = Column(String(255), nullable=True)
    embedding_id = Column(String(100), nullable=True)

    document = relationship("KnowledgeDocumentRecord", back_populates="chunks")

class RecommendationRecord(Base):
    __tablename__ = "recommendations"

    id = Column(String, primary_key=True, default=generate_uuid)
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=True)
    profile_id = Column(String, ForeignKey("environmental_profiles.id"), nullable=True)
    
    what_to_do = Column(Text, nullable=False)
    why_it_works = Column(Text, nullable=False)
    impacted_metrics_json = Column(JSON, nullable=False) # list of string metrics
    expected_impact = Column(Text, nullable=False)
    time_horizon = Column(String(100), nullable=False) # Short, Medium, Long
    confidence = Column(String(50), nullable=False) # High, Medium, Low
    
    created_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="recommendations")
    profile = relationship("EnvironmentalProfile", back_populates="recommendations")
    evidence_sources = relationship("EvidenceSourceRecord", back_populates="recommendation", cascade="all, delete-orphan")

class EvidenceSourceRecord(Base):
    __tablename__ = "evidence_sources"

    id = Column(String, primary_key=True, default=generate_uuid)
    recommendation_id = Column(String, ForeignKey("recommendations.id"), nullable=False)
    document_id = Column(String, ForeignKey("knowledge_documents.id"), nullable=True)
    
    title = Column(String(255), nullable=False)
    citation = Column(Text, nullable=False)
    relevant_snippet = Column(Text, nullable=False)
    relevance_score = Column(Float, nullable=True)

    recommendation = relationship("RecommendationRecord", back_populates="evidence_sources")
    document = relationship("KnowledgeDocumentRecord", back_populates="evidence_sources")
