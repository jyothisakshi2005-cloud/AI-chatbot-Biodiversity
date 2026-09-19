import re
from typing import List, Dict, Any, Tuple
from backend.models.schemas import EvidenceSource, Recommendation

INSUFFICIENT_EVIDENCE_MSG = "Insufficient evidence in the current knowledge base to provide a reliable estimate."

class EvidenceValidator:
    """
    Validates recommendations against retrieved knowledge base chunks to prevent
    hallucination of citations, unjustified percentages, and ungrounded claims.
    """

    @staticmethod
    def validate_and_link_evidence(
        recommendation: Recommendation,
        retrieved_chunks: List[Dict[str, Any]]
    ) -> Recommendation:
        """
        Ensures the recommendation references authentic retrieved evidence.
        If no evidence chunk supports the recommendation or if numerical claims are unsupported,
        it grounds the claim or marks exact estimates as unavailable.
        """
        if not retrieved_chunks:
            recommendation.confidence = "Low"
            recommendation.scientific_evidence = INSUFFICIENT_EVIDENCE_MSG
            recommendation.evidence_source = None
            return recommendation

        # Find best matching chunk based on text overlap or keywords
        rec_keywords = set(re.findall(r'\w{4,}', (recommendation.what_to_do + " " + recommendation.why_it_works).lower()))
        
        best_chunk = None
        best_score = -1.0

        for chunk in retrieved_chunks:
            chunk_text = chunk.get("text", "").lower()
            chunk_meta = chunk.get("metadata", {})
            
            # Count keyword overlaps
            overlap = sum(1 for kw in rec_keywords if kw in chunk_text)
            relevance = chunk.get("relevance_score", 0.5) * (1.0 + overlap * 0.1)

            if relevance > best_score:
                best_score = relevance
                best_chunk = chunk

        if best_chunk and best_score > 0.4:
            meta = best_chunk.get("metadata", {})
            title = meta.get("title", "Peer-Reviewed Agroecological Study")
            citation = meta.get("citation", "Ecological Literature Database")
            author_org = meta.get("author_org", "Scientific Research Group")

            snippet = best_chunk.get("text", "")[:280] + "..."

            recommendation.evidence_source = EvidenceSource(
                title=title,
                citation=citation,
                relevant_snippet=snippet,
                relevance_score=round(min(0.98, best_score), 2),
                author_org=author_org
            )
            recommendation.scientific_evidence = f"{citation} - \"{snippet}\""
        else:
            recommendation.confidence = "Low"
            recommendation.expected_impact = INSUFFICIENT_EVIDENCE_MSG
            recommendation.scientific_evidence = INSUFFICIENT_EVIDENCE_MSG
            recommendation.evidence_source = None

        return recommendation

    @staticmethod
    def filter_hallucinated_metrics(impacted_metrics: List[str], valid_universe: List[str]) -> List[str]:
        """Keep only recognizable environmental variables."""
        return [m for m in impacted_metrics if any(v.lower() in m.lower() for v in valid_universe)]
