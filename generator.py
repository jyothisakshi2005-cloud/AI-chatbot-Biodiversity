from typing import List, Dict, Any
from backend.models.schemas import EnvironmentalData, Recommendation
from backend.services.evidence_validator import EvidenceValidator

class RecommendationEngine:
    """
    Generates tailored, specific, and non-obvious biodiversity recommendations.
    Every recommendation is bound to scientific evidence, explicit time horizons,
    confidence ratings, and verified impacted metrics.
    """

    def generate(
        self,
        data: EnvironmentalData,
        retrieved_evidence: List[Dict[str, Any]],
        detected_interactions: List[str]
    ) -> List[Recommendation]:
        recommendations = []

        # Extract conditions
        v_soc = data.soil.organic_carbon if data.soil else None
        v_ph = data.soil.ph if data.soil else None
        v_rainfall = str(data.climate.rainfall).lower() if (data.climate and data.climate.rainfall) else ""
        v_crop = str(data.land.crop).lower() if (data.land and data.land.crop) else ""
        v_frag = str(data.land.habitat_fragmentation).lower() if (data.land and data.land.habitat_fragmentation) else ""
        v_poll = str(data.human_impact.pollution).lower() if (data.human_impact and data.human_impact.pollution) else ""

        # Strategy 1: Dryland Legume-Cover-Crop & Agroforestry Nexus
        # Conditions: Low SOC or Low rainfall or Monoculture
        if (v_soc is not None and v_soc < 1.0) or "low" in v_rainfall or "wheat" in v_crop or "monoculture" in v_crop:
            rec1 = Recommendation(
                what_to_do="Introduce deep-rooting legume-based cover crops (e.g., cowpea, hairy vetch) and contour agroforestry windbreaks.",
                why_it_works=(
                    "Under low precipitation and depleted soil carbon, legume root exudates stimulate arbuscular mycorrhizal fungi, "
                    "re-establishing soil aggregate stability. The legume biomass fixes atmospheric nitrogen biologically, while tree strips "
                    "reduce wind shear, minimizing surface evaporation and increasing rainwater infiltration by up to 35%."
                ),
                impacted_metrics=[
                    "Soil Organic Carbon",
                    "Soil Moisture Retention",
                    "Microbial Diversity",
                    "Available Nitrogen",
                    "Habitat Diversity"
                ],
                expected_impact="Measurable stabilization of soil moisture within 12 months; gradual 0.15% to 0.25% accretion of SOC over 36 months.",
                time_horizon="Medium term (1–3 years)",
                confidence="High",
                scientific_evidence=""
            )
            recommendations.append(EvidenceValidator.validate_and_link_evidence(rec1, retrieved_evidence))

            rec_till = Recommendation(
                what_to_do="Adopt continuous zero-tillage / conservation tillage with 30%+ crop residue retention.",
                why_it_works=(
                    "Clean inversion tillage in semi-arid environments oxidizes organic matter and destroys fungal hyphal networks. "
                    "Leaving wheat crop residues creates a protective surface mulch that shields soil from solar radiation, suppresses weed competition, "
                    "and protects soil fauna."
                ),
                impacted_metrics=[
                    "Soil Moisture",
                    "Soil Organic Carbon",
                    "Microbial Biomass",
                    "Erosion Resistance"
                ],
                expected_impact="Reduces topsoil evaporation loss by 20-30% and preserves soil biological structure.",
                time_horizon="Short term (0–12 months)",
                confidence="High",
                scientific_evidence=""
            )
            recommendations.append(EvidenceValidator.validate_and_link_evidence(rec_till, retrieved_evidence))

        # Strategy 2: Ecological Hedgerow & Flowering Corridor Matrix
        # Conditions: Habitat fragmentation or pollinator crash or intensive farming
        if "severe" in v_frag or "high" in v_frag or "moderate" in v_frag or (data.biodiversity and data.biodiversity.pollinator_diversity in ["low", "critically low"]):
            rec2 = Recommendation(
                what_to_do="Establish 4 to 6-meter-wide multi-species native flowering buffer strips and hedgerow corridors every 250 meters.",
                why_it_works=(
                    "Spatial patch distances exceeding 300 meters isolate native solitary bees and hoverflies. Continuous floral corridors "
                    "provide uninterrupted nectar corridors across the landscape, enabling gene flow and supplying nesting substrates "
                    "that boost natural biological pest predation."
                ),
                impacted_metrics=[
                    "Pollinator Diversity",
                    "Habitat Diversity",
                    "Native Species Ratio",
                    "Natural Pest Control"
                ],
                expected_impact="Rapid recovery of insect visitation within 12 months; doubling of native bee nesting diversity over 2–3 years.",
                time_horizon="Short to Medium term (1–2 years)",
                confidence="High",
                scientific_evidence=""
            )
            recommendations.append(EvidenceValidator.validate_and_link_evidence(rec2, retrieved_evidence))

        # Strategy 3: Biochar-Compost Buffering & Remediation
        # Conditions: Acidic soil or high pollution or chemical intensity
        if (v_ph is not None and v_ph < 6.0) or any(p in v_poll for p in ["high", "chemical", "fertilizer", "pesticide"]):
            rec3 = Recommendation(
                what_to_do="Apply conditioned agricultural biochar co-composted with manure at 5-10 tonnes/ha and introduce mycorrhizal inoculants.",
                why_it_works=(
                    "In acidified or agrochemical-saturated soils, biochar acts as a high-surface-area buffer, neutralizing phytotoxic free aluminum, "
                    "raising soil pH, and adsorbing pesticide residues to provide protected porous niches for reintroduced soil microbes."
                ),
                impacted_metrics=[
                    "Soil pH",
                    "Soil Organic Carbon",
                    "Microbial Diversity",
                    "Cation Exchange Capacity",
                    "Toxicity Mitigation"
                ],
                expected_impact="Immediate pH buffering within 60 days; sustained recovery of beneficial soil bacteria and detritivores over 24 months.",
                time_horizon="Short to Medium term (6 months – 2 years)",
                confidence="High",
                scientific_evidence=""
            )
            recommendations.append(EvidenceValidator.validate_and_link_evidence(rec3, retrieved_evidence))

        # Strategy 4: Microrefugia and Vegetated Swales
        # Conditions: Low rainfall or drought or vulnerable species
        if "drought" in v_rainfall or "erratic" in v_rainfall or (data.climate and data.climate.drought_conditions and "drought" in str(data.climate.drought_conditions).lower()):
            rec4 = Recommendation(
                what_to_do="Construct on-contour vegetated bioswales and ephemeral retention ponds to serve as biodiversity microrefugia.",
                why_it_works=(
                    "Topographical swales decelerate flash runoff during erratic storms, routing precipitation into shallow sub-surface water tables. "
                    "The localized microclimate lowers surrounding canopy temperature by 2–3.5°C, providing vital hydration sanctuaries for vulnerable taxa."
                ),
                impacted_metrics=[
                    "Water Infiltration",
                    "Aquifer Recharge",
                    "Microclimate Buffering",
                    "Species Richness"
                ],
                expected_impact="Captures up to 80% of storm runoff; stabilizes localized relative humidity during heat extremes.",
                time_horizon="Short term for physical water capture (1–3 months); Medium term for riparian vegetation (1–2 years)",
                confidence="High",
                scientific_evidence=""
            )
            recommendations.append(EvidenceValidator.validate_and_link_evidence(rec4, retrieved_evidence))

        # Ensure at least 2 high quality recommendations
        if len(recommendations) < 2:
            rec_general = Recommendation(
                what_to_do="Diversify crop rotations with perennial native grasses and leguminous nitrogen-fixers.",
                why_it_works="Perennial root architectures enhance subterranean carbon inputs and improve soil physical aggregation.",
                impacted_metrics=["Soil Organic Carbon", "Habitat Diversity", "Microbial Diversity"],
                expected_impact="Long-term resilience against climatic extremes and progressive restoration of baseline biodiversity.",
                time_horizon="Medium term (2–3 years)",
                confidence="Medium",
                scientific_evidence=""
            )
            recommendations.append(EvidenceValidator.validate_and_link_evidence(rec_general, retrieved_evidence))

        return recommendations

recommendation_engine = RecommendationEngine()
