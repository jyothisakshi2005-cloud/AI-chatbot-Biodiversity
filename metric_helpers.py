from typing import Dict, Any, List, Tuple
from backend.models.schemas import EnvironmentalData

def calculate_data_completeness(data: EnvironmentalData) -> Tuple[int, List[str], List[str]]:
    """
    Calculates percentage of known metrics and returns lists of present and missing metrics.
    """
    core_fields = {
        "Soil Organic Carbon": data.soil.organic_carbon if data.soil else None,
        "Soil pH": data.soil.ph if data.soil else None,
        "Soil Moisture": data.soil.moisture if data.soil else None,
        "Rainfall": data.climate.rainfall if data.climate else None,
        "Temperature": data.climate.temperature if data.climate else None,
        "Land Use": data.land.land_use if data.land else None,
        "Crop System": data.land.crop if data.land else None,
        "Habitat Fragmentation": data.land.habitat_fragmentation if data.land else None,
        "Species Richness": data.biodiversity.species_richness if data.biodiversity else None,
        "Pollinator Diversity": data.biodiversity.pollinator_diversity if data.biodiversity else None,
        "Pollution Level": data.human_impact.pollution if data.human_impact else None,
        "Deforestation Indicator": data.human_impact.deforestation if data.human_impact else None,
        "Geographic Region": data.region
    }

    present = [k for k, v in core_fields.items() if v is not None and v != ""]
    missing = [k for k, v in core_fields.items() if v is None or v == ""]
    completeness_pct = int((len(present) / len(core_fields)) * 100)

    return completeness_pct, present, missing

def evaluate_health_overview(data: EnvironmentalData) -> Dict[str, Dict[str, Any]]:
    """
    Evaluates 6 key environmental health dimensions on a 0-100 score with status rating.
    """
    # 1. Soil Health
    soil_score = 50
    soil_status = "Moderate"
    if data.soil:
        if data.soil.organic_carbon is not None:
            if data.soil.organic_carbon < 0.6:
                soil_score -= 25
            elif data.soil.organic_carbon > 1.5:
                soil_score += 25
        if data.soil.ph is not None:
            if data.soil.ph < 5.5 or data.soil.ph > 8.2:
                soil_score -= 20
            elif 6.2 <= data.soil.ph <= 7.5:
                soil_score += 15
        if data.soil.fertility == "low":
            soil_score -= 15

    soil_score = max(10, min(95, soil_score))
    soil_status = "Degraded" if soil_score < 40 else "Sub-optimal" if soil_score < 65 else "Healthy"

    # 2. Biodiversity
    bio_score = 50
    if data.biodiversity:
        if data.biodiversity.species_richness == "low":
            bio_score -= 25
        elif data.biodiversity.species_richness == "high":
            bio_score += 25
        if data.biodiversity.pollinator_diversity in ["low", "critically low"]:
            bio_score -= 20
        if data.biodiversity.microbial_diversity in ["depleted", "severely depleted"]:
            bio_score -= 15

    bio_score = max(10, min(95, bio_score))
    bio_status = "Critical Risk" if bio_score < 35 else "Vulnerable" if bio_score < 65 else "Resilient"

    # 3. Water Availability
    water_score = 50
    if data.climate and data.climate.rainfall:
        if "low" in data.climate.rainfall.lower():
            water_score -= 25
        elif "high" in data.climate.rainfall.lower():
            water_score += 20
    if data.soil and data.soil.moisture:
        if data.soil.moisture < 18:
            water_score -= 20
        elif data.soil.moisture > 30:
            water_score += 15

    water_score = max(10, min(95, water_score))
    water_status = "Severe Deficit" if water_score < 35 else "Constrained" if water_score < 65 else "Adequate"

    # 4. Climate Risk
    climate_score = 50
    if data.climate:
        if data.climate.drought_conditions and "drought" in data.climate.drought_conditions.lower():
            climate_score += 25
        if data.climate.rainfall_pattern and "erratic" in data.climate.rainfall_pattern.lower():
            climate_score += 15

    climate_score = max(15, min(90, climate_score))
    climate_status = "High Vulnerability" if climate_score > 65 else "Moderate Vulnerability" if climate_score > 40 else "Low Vulnerability"

    # 5. Land Use
    land_score = 50
    if data.land:
        if data.land.land_use and "monoculture" in data.land.land_use.lower():
            land_score -= 20
        if data.land.crop and "monoculture" in data.land.crop.lower():
            land_score -= 15
        if data.land.habitat_fragmentation and "severe" in data.land.habitat_fragmentation.lower():
            land_score -= 25

    land_score = max(10, min(90, land_score))
    land_status = "Fragmented Monoculture" if land_score < 40 else "Simplified Agroecosystem" if land_score < 65 else "Diverse Landscape"

    # 6. Human Impact
    impact_score = 40
    if data.human_impact:
        if data.human_impact.pollution and any(k in data.human_impact.pollution.lower() for k in ["high", "chemical", "pesticide"]):
            impact_score += 35
        if data.human_impact.agricultural_intensity and "high" in data.human_impact.agricultural_intensity.lower():
            impact_score += 20
        if data.human_impact.deforestation and "historic" in data.human_impact.deforestation.lower():
            impact_score += 15

    impact_score = max(10, min(95, impact_score))
    impact_status = "Severe Pressure" if impact_score > 65 else "Moderate Pressure" if impact_score > 35 else "Low Pressure"

    return {
        "soil_health": {"score": soil_score, "status": soil_status},
        "biodiversity": {"score": bio_score, "status": bio_status},
        "water_availability": {"score": water_score, "status": water_status},
        "climate_risk": {"score": climate_score, "status": climate_status},
        "land_use": {"score": land_score, "status": land_status},
        "human_impact": {"score": impact_score, "status": impact_status}
    }
