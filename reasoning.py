import os
import json
from typing import Dict, Any, List, Optional
from backend.models.schemas import EnvironmentalData, AssessmentResponse, EvidenceSource, Recommendation
from backend.rag.vectorstore import retriever
from backend.reasoning.engine import reasoning_engine
from backend.recommendations.generator import recommendation_engine

def format_context(data: EnvironmentalData) -> str:
    parts = []
    if data.region:
        parts.append(f"Region/Climate Zone: {data.region}")
    if data.soil:
        s = data.soil
        s_parts = []
        if s.organic_carbon is not None: s_parts.append(f"Organic Carbon={s.organic_carbon}%")
        if s.ph is not None: s_parts.append(f"pH={s.ph}")
        if s.moisture is not None: s_parts.append(f"Moisture={s.moisture}%")
        if s.moisture_level: s_parts.append(f"Moisture Level={s.moisture_level}")
        if s.fertility: s_parts.append(f"Fertility={s.fertility}")
        if s.degradation_indicators: s_parts.append(f"Degradation={s.degradation_indicators}")
        if s_parts: parts.append(f"Soil Health: {', '.join(s_parts)}")

    if data.climate:
        c = data.climate
        c_parts = []
        if c.rainfall: c_parts.append(f"Rainfall={c.rainfall}")
        if c.rainfall_amount_mm: c_parts.append(f"Amount={c.rainfall_amount_mm}mm")
        if c.rainfall_pattern: c_parts.append(f"Pattern={c.rainfall_pattern}")
        if c.temperature is not None: c_parts.append(f"Temperature={c.temperature}°C")
        if c.drought_conditions: c_parts.append(f"Drought={c.drought_conditions}")
        if c_parts: parts.append(f"Climate: {', '.join(c_parts)}")

    if data.land:
        l = data.land
        l_parts = []
        if l.land_use: l_parts.append(f"Land Use={l.land_use}")
        if l.crop: l_parts.append(f"Crop={l.crop}")
        if l.cropping_system: l_parts.append(f"System={l.cropping_system}")
        if l.habitat_fragmentation: l_parts.append(f"Fragmentation={l.habitat_fragmentation}")
        if l_parts: parts.append(f"Land Cover: {', '.join(l_parts)}")

    if data.biodiversity:
        b = data.biodiversity
        b_parts = []
        if b.species_richness: b_parts.append(f"Species Richness={b.species_richness}")
        if b.pollinator_diversity: b_parts.append(f"Pollinator Diversity={b.pollinator_diversity}")
        if b.microbial_diversity: b_parts.append(f"Microbial Diversity={b.microbial_diversity}")
        if b_parts: parts.append(f"Biodiversity Status: {', '.join(b_parts)}")

    if data.human_impact:
        h = data.human_impact
        h_parts = []
        if h.pollution: h_parts.append(f"Pollution={h.pollution}")
        if h.deforestation: h_parts.append(f"Deforestation={h.deforestation}")
        if h.agricultural_intensity: h_parts.append(f"Intensity={h.agricultural_intensity}")
        if h_parts: parts.append(f"Human Disturbance: {', '.join(h_parts)}")

    return "\n".join(parts) if parts else "No specific conditions observed."

def build_retrieval_query(data: EnvironmentalData) -> str:
    terms = []
    if data.soil and data.soil.organic_carbon is not None:
        terms.append(f"soil organic carbon {data.soil.organic_carbon}%")
    if data.soil and data.soil.ph is not None:
        terms.append(f"soil pH {data.soil.ph}")
    if data.climate and data.climate.rainfall:
        terms.append(f"{data.climate.rainfall} rainfall")
    if data.land and data.land.crop:
        terms.append(f"{data.land.crop}")
    if data.land and data.land.habitat_fragmentation:
        terms.append(f"habitat fragmentation {data.land.habitat_fragmentation}")
    if data.human_impact and data.human_impact.pollution:
        terms.append(f"pollution {data.human_impact.pollution}")
    if data.region:
        terms.append(f"{data.region}")

    return " ".join(terms) if terms else "biodiversity conservation soil health"

def get_assessment(data: EnvironmentalData, retrieved_evidence: Optional[List[Dict[str, Any]]] = None) -> AssessmentResponse:
    # 1. Vector Retrieval if not provided
    if retrieved_evidence is None:
        query = build_retrieval_query(data)
        retrieved_evidence = retriever.search(query, n_results=4)

    # 2. Multi-Metric Reasoning across >= 3 variables
    analysis = reasoning_engine.analyze(data, retrieved_evidence)

    # 3. Recommendation Generation
    recommendations = recommendation_engine.generate(
        data=data,
        retrieved_evidence=retrieved_evidence,
        detected_interactions=analysis["detected_interactions"]
    )

    # Compile observed conditions dict
    observed = {
        "region": data.region or "Not specified",
        "soil": f"SOC: {data.soil.organic_carbon if data.soil and data.soil.organic_carbon is not None else 'N/A'}%, pH: {data.soil.ph if data.soil and data.soil.ph is not None else 'N/A'}",
        "climate": f"Rainfall: {data.climate.rainfall if data.climate and data.climate.rainfall else 'N/A'}, Temp: {data.climate.temperature if data.climate and data.climate.temperature is not None else 'N/A'}°C",
        "land": f"Land Use: {data.land.land_use if data.land and data.land.land_use else 'N/A'}, Crop: {data.land.crop if data.land and data.land.crop else 'N/A'}, Fragmentation: {data.land.habitat_fragmentation if data.land and data.land.habitat_fragmentation else 'N/A'}",
        "biodiversity": f"Species Richness: {data.biodiversity.species_richness if data.biodiversity and data.biodiversity.species_richness else 'N/A'}, Pollinators: {data.biodiversity.pollinator_diversity if data.biodiversity and data.biodiversity.pollinator_diversity else 'N/A'}",
        "human_impact": f"Pollution: {data.human_impact.pollution if data.human_impact and data.human_impact.pollution else 'N/A'}"
    }

    # Extract all evidence sources from recommendations and retrieved documents
    sources = []
    seen_citations = set()
    for rec in recommendations:
        if rec.evidence_source and rec.evidence_source.citation not in seen_citations:
            sources.append(rec.evidence_source)
            seen_citations.add(rec.evidence_source.citation)

    for item in retrieved_evidence:
        meta = item.get("metadata", {})
        citation = meta.get("citation", "Scientific Report")
        if citation not in seen_citations:
            sources.append(EvidenceSource(
                title=meta.get("title", "Environmental Research Study"),
                citation=citation,
                relevant_snippet=item.get("text", "")[:260] + "...",
                relevance_score=item.get("relevance_score", 0.8),
                author_org=meta.get("author_org", "Scientific Organization")
            ))
            seen_citations.add(citation)

    # Summary of impacted metrics
    impacted_set = set()
    for r in recommendations:
        for m in r.impacted_metrics:
            impacted_set.add(m)

    # Next missing information
    missing_info = analysis.get("missing_metrics", [])
    next_question = f"For higher resolution modeling, could you specify: {missing_info[0]}?" if missing_info else None

    # Check if Gemini API is available and user wants LLM refinement
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key and api_key != "mock_key":
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro", google_api_key=api_key, temperature=0.1)
            docs_text = "\n\n".join([f"Source: {s.citation}\nExcerpt: {s.relevant_snippet}" for s in sources[:3]])
            llm_prompt = f"""
            You are a senior AI environmental scientist. Refine this assessment based on the conditions and retrieved scientific documents:
            Conditions: {format_context(data)}
            Documents: {docs_text}
            Draft Multi-Metric Reasoning: {analysis['multi_metric_reasoning']}
            
            Return JSON with keys:
            - assessment (2 sentences)
            - multi_metric_reasoning (detailed scientific explanation of feedback loops)
            """
            resp = llm.invoke(llm_prompt)
            content = resp.content.strip()
            if content.startswith("```json"):
                content = content.replace("```json", "", 1).replace("```", "")
            parsed = json.loads(content)
            if "assessment" in parsed: analysis["assessment"] = parsed["assessment"]
            if "multi_metric_reasoning" in parsed: analysis["multi_metric_reasoning"] = parsed["multi_metric_reasoning"]
        except Exception as e:
            # Safe deterministic fallback
            print(f"Gemini LLM synthesis optional step skipped/failed: {e}")

    return AssessmentResponse(
        assessment=analysis["assessment"],
        key_environmental_drivers=analysis["key_environmental_drivers"],
        multi_metric_reasoning=analysis["multi_metric_reasoning"],
        observed_conditions=observed,
        risk_overview=analysis["risk_overview"],
        recommendations=recommendations,
        impacted_metrics_summary=sorted(list(impacted_set)),
        time_horizon_summary="Short-term stabilization (0–12m), Medium-term biophysical recovery (1–3y), Long-term ecological resilience (3+y)",
        confidence_level="High" if len(sources) >= 2 else "Medium",
        evidence_sources=sources,
        missing_information=missing_info[:4] if missing_info else [],
        next_question=next_question
    )
