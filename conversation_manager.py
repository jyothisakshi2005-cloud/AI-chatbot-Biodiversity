import re
from typing import Optional, Dict, Any, Tuple, List
from sqlalchemy.orm import Session
from backend.models.schemas import EnvironmentalData, SoilMetrics, ClimateMetrics, LandMetrics, BiodiversityMetrics, HumanImpactMetrics
from backend.models.db_models import Conversation, Message

class ConversationManager:
    """
    Maintains multi-turn conversation memory, extracts environmental metrics
    from natural language statements, identifies missing information, and asks
    targeted clarifying questions.
    """

    def process_turn(
        self,
        db: Session,
        conversation_id: Optional[str],
        user_message: str,
        incoming_context: Optional[EnvironmentalData] = None
    ) -> Tuple[str, EnvironmentalData, bool, List[str], str]:
        """
        Process a single turn of conversation.
        Returns:
            conversation_id: str
            accumulated_context: EnvironmentalData
            requires_more_info: bool
            missing_fields: List[str]
            assistant_message: str
        """
        # 1. Retrieve or create conversation
        conversation = None
        if conversation_id:
            conversation = db.query(Conversation).filter_by(id=conversation_id).first()

        if not conversation:
            conversation = Conversation(title=user_message[:40] + "...")
            db.add(conversation)
            db.commit()
            db.refresh(conversation)

        # 2. Reconstruct accumulated context from past messages
        accumulated_dict = {}
        past_messages = db.query(Message).filter_by(conversation_id=conversation.id).order_by(Message.created_at).all()
        for past_msg in past_messages:
            if past_msg.extracted_context_json:
                self._deep_merge(accumulated_dict, past_msg.extracted_context_json)

        # 3. Merge incoming context if provided explicitly
        if incoming_context:
            self._deep_merge(accumulated_dict, incoming_context.model_dump(exclude_unset=True, exclude_none=True))

        # 4. Extract environmental variables from current user message text
        extracted_from_text = self._extract_from_text(user_message)
        self._deep_merge(accumulated_dict, extracted_from_text)

        # Build EnvironmentalData object
        current_data = EnvironmentalData(**accumulated_dict)

        # 5. Check what essential environmental metrics are still missing
        missing_fields = self._determine_missing_fields(current_data)

        # Determine if we have at least 3 essential variables to perform multi-metric reasoning
        connected_vars = self._count_known_variables(current_data)
        requires_more_info = connected_vars < 3

        # Check for general knowledge question
        is_general_question = any(word in user_message.lower() for word in ['what', 'why', 'how', 'explain', 'tell me about', 'biodiversity']) and connected_vars == 0

        # Formulate response or clarifying question
        if is_general_question:
            from backend.rag.vectorstore import retriever
            results = retriever.search(user_message, n_results=1)
            if results:
                snippet = results[0]['text']
                assistant_reply = f"**Knowledge Base Answer:** {snippet}\n\nTo perform a site-specific ecological assessment, I still need more data."
            else:
                assistant_reply = "I couldn't find specific information on that in the knowledge base.\n\n" + self._generate_clarifying_prompt(current_data, missing_fields)
        elif requires_more_info:
            assistant_reply = self._generate_clarifying_prompt(current_data, missing_fields)
        else:
            assistant_reply = (
                f"Thank you. I have mapped {connected_vars} active environmental variables across soil, climate, and land-use. "
                "Executing multi-metric ecological retrieval and scientific reasoning now..."
            )

        # Persist User and Assistant messages into Database
        user_record = Message(
            conversation_id=conversation.id,
            role="user",
            content=user_message,
            extracted_context_json=current_data.model_dump(mode="json")
        )
        db.add(user_record)

        asst_record = Message(
            conversation_id=conversation.id,
            role="assistant",
            content=assistant_reply,
            requires_more_info=1 if requires_more_info else 0,
            extracted_context_json=current_data.model_dump(mode="json")
        )
        db.add(asst_record)
        db.commit()

        return conversation.id, current_data, requires_more_info, missing_fields, assistant_reply

    def _count_known_variables(self, data: EnvironmentalData) -> int:
        count = 0
        if data.soil:
            if data.soil.organic_carbon is not None: count += 1
            if data.soil.ph is not None: count += 1
            if data.soil.moisture is not None: count += 1
        if data.climate:
            if data.climate.rainfall: count += 1
            if data.climate.temperature is not None: count += 1
        if data.land:
            if data.land.crop: count += 1
            if data.land.land_use: count += 1
            if data.land.habitat_fragmentation: count += 1
        if data.biodiversity:
            if data.biodiversity.species_richness: count += 1
            if data.biodiversity.pollinator_diversity: count += 1
        if data.human_impact:
            if data.human_impact.pollution: count += 1
            if data.human_impact.deforestation: count += 1
        if data.region:
            count += 1
        return count

    def _determine_missing_fields(self, data: EnvironmentalData) -> List[str]:
        missing = []
        if not data.soil or data.soil.organic_carbon is None:
            missing.append("Soil organic carbon % (e.g., 0.3% or 1.2%)")
        if not data.climate or not data.climate.rainfall:
            missing.append("Rainfall pattern or volume (e.g., low, 300mm, erratic)")
        if not data.land or (not data.land.crop and not data.land.land_use):
            missing.append("Land use or cropping system (e.g., monoculture wheat, agroforestry)")
        if not data.region:
            missing.append("Region or climate zone (e.g., semi-arid, Mediterranean, temperate)")
        if not data.biodiversity or not data.biodiversity.species_richness:
            missing.append("Current biodiversity / species richness status (e.g., declining, low, stable)")
        return missing

    def _generate_clarifying_prompt(self, current_data: EnvironmentalData, missing: List[str]) -> str:
        prompt_lines = [
            "I am investigating the environmental drivers behind your ecosystem conditions.",
            "To perform rigorous multi-metric reasoning across at least 3 environmental variables, please provide:",
            ""
        ]
        for idx, m in enumerate(missing[:4], 1):
            prompt_lines.append(f"{idx}. {m}")

        prompt_lines.append("")
        prompt_lines.append("You can provide these directly in chat, use the 'Structured Input' button, or paste JSON.")
        return "\n".join(prompt_lines)

    def _extract_from_text(self, text: str) -> Dict[str, Any]:
        """Rule-based natural language entity extraction for environmental metrics."""
        result: Dict[str, Any] = {
            "soil": {},
            "climate": {},
            "land": {},
            "biodiversity": {},
            "human_impact": {}
        }
        lower = text.lower()

        # Soil Carbon: e.g. "soil carbon is 0.3%", "organic carbon 0.4%", "0.3% soc"
        soc_match = re.search(r'(?:soil(?:\s+organic)?\s+carbon|soc|organic\s+carbon)(?:\s+is|\s*[:=])?\s*([\d\.]+)\s*%?', lower)
        if not soc_match:
            soc_match = re.search(r'([\d\.]+)\s*%\s*(?:soil(?:\s+organic)?\s+carbon|soc)', lower)
        if soc_match:
            try:
                result["soil"]["organic_carbon"] = float(soc_match.group(1))
            except ValueError:
                pass

        # Soil pH: e.g. "soil ph is 6.8", "ph 4.8", "ph: 7.2"
        ph_match = re.search(r'(?:soil\s+)?ph(?:\s+is|\s*[:=])?\s*([\d\.]+)', lower)
        if ph_match:
            try:
                result["soil"]["ph"] = float(ph_match.group(1))
            except ValueError:
                pass

        # Soil Moisture: e.g. "moisture is low", "soil moisture 14%"
        if "low soil moisture" in lower or "low moisture" in lower:
            result["soil"]["moisture_level"] = "low"
        elif "high moisture" in lower:
            result["soil"]["moisture_level"] = "high"

        # Climate / Rainfall: e.g. "rainfall is low", "low rainfall", "erratic rain"
        if "low rainfall" in lower or "rainfall is low" in lower or "dry rainfall" in lower:
            result["climate"]["rainfall"] = "low"
        elif "moderate rainfall" in lower or "medium rainfall" in lower:
            result["climate"]["rainfall"] = "moderate"
        elif "high rainfall" in lower:
            result["climate"]["rainfall"] = "high"
        elif "erratic rainfall" in lower:
            result["climate"]["rainfall"] = "erratic"

        # Drought
        if "drought" in lower:
            result["climate"]["drought_conditions"] = "severe seasonal drought"

        # Land Use / Crop
        if "monoculture wheat" in lower or ("wheat" in lower and "monoculture" in lower):
            result["land"]["crop"] = "monoculture wheat"
            result["land"]["land_use"] = "monoculture agriculture"
        elif "wheat" in lower:
            result["land"]["crop"] = "wheat"
        elif "maize" in lower or "corn" in lower:
            result["land"]["crop"] = "maize"

        if "monoculture" in lower:
            result["land"]["cropping_system"] = "monoculture"
        if "intercropping" in lower:
            result["land"]["cropping_system"] = "intercropping"
        if "agroforestry" in lower:
            result["land"]["cropping_system"] = "agroforestry"

        # Habitat Fragmentation
        if "fragmented" in lower or "fragmentation" in lower:
            result["land"]["habitat_fragmentation"] = "high"

        # Biodiversity
        if "biodiversity is declining" in lower or "declining biodiversity" in lower or "loss of biodiversity" in lower:
            result["biodiversity"]["species_richness"] = "declining"
            result["biodiversity"]["species_survival_indicators"] = "declining"
        if "low species richness" in lower:
            result["biodiversity"]["species_richness"] = "low"
        if "pollinator crash" in lower or "low pollinator" in lower or "no bees" in lower:
            result["biodiversity"]["pollinator_diversity"] = "critically low"

        # Human Impact / Pollution / Deforestation
        if "high pollution" in lower or "chemical pollution" in lower:
            result["human_impact"]["pollution"] = "high chemical pollution"
        if "deforestation" in lower:
            result["human_impact"]["deforestation"] = "moderate"

        # Region
        if "semi-arid" in lower or "semi arid" in lower:
            result["region"] = "semi-arid"
            result["climate"]["climate_zone"] = "semi-arid"
        elif "subtropical" in lower:
            result["region"] = "subtropical"
            result["climate"]["climate_zone"] = "subtropical"
        elif "mediterranean" in lower:
            result["region"] = "Mediterranean"
            result["climate"]["climate_zone"] = "Mediterranean"

        # Clean empty dicts
        cleaned = {k: v for k, v in result.items() if v}
        return cleaned

    def _deep_merge(self, base: Dict[str, Any], update: Dict[str, Any]) -> None:
        for k, v in update.items():
            if isinstance(v, dict) and k in base and isinstance(base[k], dict):
                self._deep_merge(base[k], v)
            elif v is not None and v != "":
                base[k] = v

conversation_manager = ConversationManager()
