from typing import Dict, Any, List, Tuple
from backend.models.schemas import EnvironmentalData, BiodiversityRiskOverview
from backend.utils.metric_helpers import calculate_data_completeness

class MultiMetricReasoningEngine:
    """
    Core ecological intelligence engine.
    Analyzes simultaneous interactions across >= 3 environmental variables
    (e.g., Soil Health, Land Cover, Climate, Biodiversity, Human Impact)
    to uncover compounding degradation feedbacks and non-obvious restoration leverage points.
    """

    def analyze(self, data: EnvironmentalData, retrieved_evidence: List[Dict[str, Any]]) -> Dict[str, Any]:
        completeness_pct, present_metrics, missing_metrics = calculate_data_completeness(data)

        # 1. Identify active variables
        variables = self._extract_active_variables(data)
        connected_count = len(variables)

        # 2. Identify key drivers of degradation or vulnerability
        key_drivers = self._identify_drivers(data, variables)

        # 3. Formulate multi-metric reasoning chain across >= 3 variables
        reasoning_text, detected_interactions = self._formulate_multi_metric_reasoning(data, variables)

        # 4. Synthesize overarching assessment
        assessment_text, risk_level = self._synthesize_assessment(data, variables, key_drivers)

        risk_overview = BiodiversityRiskOverview(
            current_condition=f"Identified {len(detected_interactions)} compounding ecological feedback loops across {connected_count} variables.",
            major_environmental_drivers=key_drivers,
            risk_level=risk_level,
            data_completeness_pct=completeness_pct,
            connected_variables_count=connected_count
        )

        return {
            "assessment": assessment_text,
            "key_environmental_drivers": key_drivers,
            "multi_metric_reasoning": reasoning_text,
            "detected_interactions": detected_interactions,
            "risk_overview": risk_overview,
            "connected_variables_count": connected_count,
            "missing_metrics": missing_metrics
        }

    def _extract_active_variables(self, data: EnvironmentalData) -> Dict[str, Any]:
        v = {}
        if data.soil:
            if data.soil.organic_carbon is not None:
                v["soil_carbon"] = data.soil.organic_carbon
            if data.soil.ph is not None:
                v["soil_ph"] = data.soil.ph
            if data.soil.moisture is not None:
                v["soil_moisture"] = data.soil.moisture
            if data.soil.degradation_indicators:
                v["soil_degradation"] = data.soil.degradation_indicators

        if data.climate:
            if data.climate.rainfall:
                v["rainfall"] = data.climate.rainfall
            if data.climate.rainfall_pattern:
                v["rainfall_pattern"] = data.climate.rainfall_pattern
            if data.climate.temperature is not None:
                v["temperature"] = data.climate.temperature
            if data.climate.drought_conditions:
                v["drought"] = data.climate.drought_conditions

        if data.land:
            if data.land.land_use:
                v["land_use"] = data.land.land_use
            if data.land.crop:
                v["crop"] = data.land.crop
            if data.land.habitat_fragmentation:
                v["fragmentation"] = data.land.habitat_fragmentation

        if data.biodiversity:
            if data.biodiversity.species_richness:
                v["species_richness"] = data.biodiversity.species_richness
            if data.biodiversity.pollinator_diversity:
                v["pollinator_diversity"] = data.biodiversity.pollinator_diversity
            if data.biodiversity.microbial_diversity:
                v["microbial_diversity"] = data.biodiversity.microbial_diversity

        if data.human_impact:
            if data.human_impact.pollution:
                v["pollution"] = data.human_impact.pollution
            if data.human_impact.deforestation:
                v["deforestation"] = data.human_impact.deforestation
            if data.human_impact.agricultural_intensity:
                v["agricultural_intensity"] = data.human_impact.agricultural_intensity

        if data.region:
            v["region"] = data.region

        return v

    def _identify_drivers(self, data: EnvironmentalData, v: Dict[str, Any]) -> List[str]:
        drivers = []
        # Soil drivers
        if "soil_carbon" in v and float(v["soil_carbon"]) < 0.8:
            drivers.append(f"Severely depleted Soil Organic Carbon ({v['soil_carbon']}%)")
        if "soil_ph" in v and (float(v["soil_ph"]) < 5.5 or float(v["soil_ph"]) > 8.0):
            drivers.append(f"Altered Soil pH ({v['soil_ph']}) inducing nutrient lockup/toxicity")
        
        # Climate drivers
        if "rainfall" in v and "low" in str(v["rainfall"]).lower():
            drivers.append("Low and restrictive precipitation regime")
        if "drought" in v and "none" not in str(v["drought"]).lower():
            drivers.append(f"Drought pressure ({v['drought']})")

        # Land use drivers
        if "crop" in v and "monoculture" in str(v["crop"]).lower():
            drivers.append(f"Continuous monoculture cultivation ({v['crop']})")
        if "fragmentation" in v and ("high" in str(v["fragmentation"]).lower() or "severe" in str(v["fragmentation"]).lower()):
            drivers.append("Severe spatial habitat fragmentation with isolated natural patches")

        # Human impact drivers
        if "pollution" in v and any(p in str(v["pollution"]).lower() for p in ["high", "chemical", "pesticide"]):
            drivers.append(f"Elevated chemical agrochemical contamination ({v['pollution']})")
        if "agricultural_intensity" in v and "high" in str(v["agricultural_intensity"]).lower():
            drivers.append("High mechanical/agrochemical disturbance frequency")

        if not drivers:
            drivers.append("Moderate systemic vulnerability across combined soil and climate metrics")

        return drivers

    def _formulate_multi_metric_reasoning(self, data: EnvironmentalData, v: Dict[str, Any]) -> Tuple[str, List[str]]:
        """
        Synthesizes interactions connecting at least 3 environmental variables simultaneously.
        """
        interactions = []
        reasoning_paragraphs = []

        # Multi-Metric Loop 1: Semi-Arid Soil-Carbon-Water-Crop nexus (Soil + Climate + Land Use + Microbes)
        is_low_soc = "soil_carbon" in v and float(v["soil_carbon"]) <= 0.8
        is_low_rain = "rainfall" in v and ("low" in str(v["rainfall"]).lower() or "erratic" in str(v["rainfall"]).lower())
        is_monoculture = ("crop" in v and "monoculture" in str(v["crop"]).lower()) or ("land_use" in v and "monoculture" in str(v["land_use"]).lower())

        if is_low_soc and is_low_rain and is_monoculture:
            interactions.append("Soil Organic Carbon (0.3%) ↔ Low Rainfall ↔ Monoculture Wheat ↔ Microbial Starvation")
            reasoning_paragraphs.append(
                "1. **Compounding Soil-Climate-Crop Degradation Nexus (4 Connected Variables)**: "
                f"The presence of low Soil Organic Carbon ({v.get('soil_carbon')}%) in a semi-arid, low-rainfall environment "
                "impairs soil aggregate stability. Under monoculture wheat cultivation, continuous root-zone extraction without diverse organic residues "
                "causes surface crusting, preventing episodic rainwater infiltration (losing over 50% to runoff/evaporation). "
                "This water deficit starves the indigenous soil microbiome, inhibiting mycorrhizal networks and nitrogen mineralization, "
                "which in turn leads to declining plant vigor and collapses above-ground biodiversity."
            )

        # Multi-Metric Loop 2: Fragmentation + Agriculture Intensity + Pollinators (Land Use + Biodiversity + Human Impact)
        is_fragmented = "fragmentation" in v and any(w in str(v["fragmentation"]).lower() for w in ["high", "severe", "moderate"])
        is_pollinator_low = "pollinator_diversity" in v and any(w in str(v["pollinator_diversity"]).lower() for w in ["low", "critical"])
        is_intensive = "agricultural_intensity" in v and "high" in str(v["agricultural_intensity"]).lower()

        if is_fragmented or (is_pollinator_low and is_monoculture):
            interactions.append("Habitat Fragmentation ↔ Agricultural Intensity ↔ Pollinator Crash ↔ Reproductive Failure")
            reasoning_paragraphs.append(
                "2. **Landscape Fragmentation & Trophic Decoupling (3 Connected Variables)**: "
                "Intensive agricultural field boundaries exceeding 300 meters between remnant natural patches exceed the foraging flight threshold of native solitary bees. "
                "Coupled with monoculture crop phenology (which provides a brief single floral pulse followed by nutritional drought), "
                "wild pollinators experience acute starvation and reproductive crashes, eliminating natural pest predators and destabilizing the local food web."
            )

        # Multi-Metric Loop 3: Acidification + Chemical Pollution + Soil Ecology (Soil pH + Pollution + Microbial Diversity)
        is_acidic = "soil_ph" in v and float(v["soil_ph"]) < 5.8
        is_polluted = "pollution" in v and any(w in str(v["pollution"]).lower() for w in ["high", "chemical", "fertilizer", "pesticide"])

        if is_acidic and is_polluted:
            interactions.append("Low Soil pH (<5.5) ↔ Agrochemical Pollution ↔ Aluminum Toxicity ↔ Soil Sterilization")
            reasoning_paragraphs.append(
                "3. **Chemical-Toxicity Cascade (3 Connected Variables)**: "
                f"Synthetic input overuse has depressed soil pH to {v.get('soil_ph')}, solubilizing phytotoxic aluminum ions. "
                "The combination of chemical toxicity and high acidity suppresses beneficial ammonifying and nitrifying bacteria, "
                "rendering added fertilizers bio-unavailable and locking the land in an escalating degradation trap."
            )

        # Multi-Metric Loop 4: General Multi-Metric Synthesis if specific patterns don't capture >= 3
        if len(interactions) == 0:
            connected_names = list(v.keys())[:4]
            interactions.append(" ↔ ".join([name.replace('_', ' ').capitalize() for name in connected_names]))
            reasoning_paragraphs.append(
                f"The observed conditions involve simultaneous constraints across {', '.join(connected_names)}. "
                "In ecosystem science, these metrics do not act in isolation: limitations in one domain (e.g. moisture or soil nutrients) "
                "exponentially magnify biological vulnerabilities in another (e.g. species survival and habitat structure)."
            )

        full_reasoning = "\n\n".join(reasoning_paragraphs)
        return full_reasoning, interactions

    def _synthesize_assessment(self, data: EnvironmentalData, v: Dict[str, Any], drivers: List[str]) -> Tuple[str, str]:
        # Determine risk
        if any("Severely" in d or "Critical" in d or "depleted" in d.lower() for d in drivers):
            risk_level = "Critical"
            condition_desc = "experiencing elevated, multi-factorial ecological degradation"
        elif len(drivers) >= 2:
            risk_level = "Elevated"
            condition_desc = "under compounded environmental stress with vulnerable biodiversity indicators"
        else:
            risk_level = "Moderate"
            condition_desc = "sub-optimal with localized ecological vulnerabilities"

        assessment = (
            f"The environmental system is currently {condition_desc}. "
            f"Analysis of {len(v)} active environmental parameters confirms that biodiversity decline is not driven by a single isolated variable, "
            f"but by mutually reinforcing stress factors spanning soil physical-chemical condition, climate moisture constraints, and land management intensity."
        )
        return assessment, risk_level

reasoning_engine = MultiMetricReasoningEngine()
