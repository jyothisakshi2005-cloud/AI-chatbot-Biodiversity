from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class SoilMetrics(BaseModel):
    ph: Optional[float] = Field(None, description="Soil pH (e.g. 6.5)")
    organic_carbon: Optional[float] = Field(None, description="Soil organic carbon percentage (e.g. 0.3%)")
    moisture: Optional[float] = Field(None, description="Soil moisture % or relative index")
    moisture_level: Optional[str] = Field(None, description="low, medium, high")
    fertility: Optional[str] = Field(None, description="low, moderate, high")
    degradation_indicators: Optional[str] = Field(None, description="erosion, compaction, salinization, none")

class ClimateMetrics(BaseModel):
    rainfall: Optional[str] = Field(None, description="low, moderate, high, erratic")
    rainfall_amount_mm: Optional[float] = Field(None, description="Annual rainfall in mm")
    rainfall_pattern: Optional[str] = Field(None, description="seasonal, erratic, unimodal, drought-prone")
    temperature: Optional[float] = Field(None, description="Average temperature in Celsius")
    drought_conditions: Optional[str] = Field(None, description="none, mild, severe, recurrent")
    climate_zone: Optional[str] = Field(None, description="arid, semi-arid, temperate, tropical, mediterranean")

class LandMetrics(BaseModel):
    land_use: Optional[str] = Field(None, description="agriculture, forest, grassland, wetland, urban, agroforestry")
    crop: Optional[str] = Field(None, description="monoculture wheat, maize, mixed, etc.")
    cropping_system: Optional[str] = Field(None, description="monoculture, intercropping, agroforestry, fallow")
    habitat_fragmentation: Optional[str] = Field(None, description="low, moderate, high, severe")
    vegetation_cover: Optional[str] = Field(None, description="bare, sparse, moderate, dense")

class BiodiversityMetrics(BaseModel):
    species_richness: Optional[str] = Field(None, description="low, moderate, high")
    habitat_diversity: Optional[str] = Field(None, description="low, moderate, high")
    pollinator_diversity: Optional[str] = Field(None, description="low, moderate, high")
    microbial_diversity: Optional[str] = Field(None, description="depleted, moderate, rich")
    native_species_ratio: Optional[float] = Field(None, description="Ratio of native species 0.0 to 1.0")
    species_survival_indicators: Optional[str] = Field(None, description="vulnerable, stable, declining")

class HumanImpactMetrics(BaseModel):
    pollution: Optional[str] = Field(None, description="none, low, moderate, high, industrial, pesticide-heavy")
    deforestation: Optional[str] = Field(None, description="none, low, moderate, severe")
    agricultural_intensity: Optional[str] = Field(None, description="low, medium, high, intensive-chemical")
    land_degradation: Optional[str] = Field(None, description="none, light, moderate, severe")
    habitat_destruction: Optional[str] = Field(None, description="none, localized, widespread")

class EnvironmentalData(BaseModel):
    region: Optional[str] = Field(None, description="e.g. semi-arid, Mediterranean, Sahel")
    latitude: Optional[float] = Field(None, description="Geographic latitude")
    longitude: Optional[float] = Field(None, description="Geographic longitude")
    soil: Optional[SoilMetrics] = Field(default_factory=SoilMetrics)
    climate: Optional[ClimateMetrics] = Field(default_factory=ClimateMetrics)
    land: Optional[LandMetrics] = Field(default_factory=LandMetrics)
    biodiversity: Optional[BiodiversityMetrics] = Field(default_factory=BiodiversityMetrics)
    human_impact: Optional[HumanImpactMetrics] = Field(default_factory=HumanImpactMetrics)

class EvidenceSource(BaseModel):
    title: str
    citation: str
    relevant_snippet: str
    relevance_score: Optional[float] = 0.85
    doi_or_url: Optional[str] = None
    author_org: Optional[str] = None

class Recommendation(BaseModel):
    what_to_do: str
    why_it_works: str
    impacted_metrics: List[str]
    expected_impact: str
    time_horizon: str # "Short (0-12 months)", "Medium (1-3 years)", "Long (3+ years)"
    confidence: str # "High", "Medium", "Low"
    scientific_evidence: str
    evidence_source: Optional[EvidenceSource] = None

class BiodiversityRiskOverview(BaseModel):
    current_condition: str
    major_environmental_drivers: List[str]
    risk_level: str # "Critical", "Elevated", "Moderate", "Stable"
    data_completeness_pct: int
    connected_variables_count: int

class AssessmentResponse(BaseModel):
    assessment: str
    key_environmental_drivers: List[str]
    multi_metric_reasoning: str
    observed_conditions: Dict[str, Any]
    risk_overview: Optional[BiodiversityRiskOverview] = None
    recommendations: List[Recommendation]
    impacted_metrics_summary: List[str]
    time_horizon_summary: str
    confidence_level: str
    evidence_sources: List[EvidenceSource]
    missing_information: Optional[List[str]] = None
    next_question: Optional[str] = None

class ChatMessage(BaseModel):
    id: Optional[str] = None
    role: str
    content: str
    created_at: Optional[str] = None

class ChatRequest(BaseModel):
    conversation_id: Optional[str] = None
    message: str
    context: Optional[EnvironmentalData] = None

class ChatResponse(BaseModel):
    conversation_id: str
    message: str
    requires_more_info: bool
    missing_fields: Optional[List[str]] = None
    extracted_context: Optional[EnvironmentalData] = None
    assessment: Optional[AssessmentResponse] = None

class EnvironmentalProfileCreate(BaseModel):
    name: Optional[str] = "Farm Assessment Profile"
    conversation_id: Optional[str] = None
    region: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    climate_zone: Optional[str] = None
    metrics: EnvironmentalData

class EnvironmentalProfileResponse(BaseModel):
    id: str
    name: str
    region: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    climate_zone: Optional[str]
    metrics: EnvironmentalData
    created_at: str

class KnowledgeSearchRequest(BaseModel):
    query: str
    limit: Optional[int] = 5
    category: Optional[str] = None

class KnowledgeSearchResultItem(BaseModel):
    document_id: str
    title: str
    author_org: str
    citation: str
    snippet: str
    relevance_score: float
    category: Optional[str] = None

class KnowledgeSearchResponse(BaseModel):
    query: str
    results: List[KnowledgeSearchResultItem]

class DocumentIngestRequest(BaseModel):
    title: str
    author_org: str
    citation: str
    publication_year: Optional[int] = None
    category: str
    summary: Optional[str] = None
    content: str

class ScenarioPreset(BaseModel):
    id: str
    title: str
    subtitle: str
    description: str
    data: EnvironmentalData
    expected_focus: List[str]
