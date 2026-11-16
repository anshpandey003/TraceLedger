
from collections.abc import Sequence

from openai import OpenAI

from backend.app.core.config import settings
from backend.app.models.claim import Claim
from backend.app.models.evidence import Evidence
from backend.app.schemas.verification import VerificationDecision
from backend.app.services.evidence_verifier import EvidenceVerifier
from backend.app.services.investigation_analysis import InvestigationAnalysis


class LLMVerifier(EvidenceVerifier):
    def __init__(self) -> None:
        self.client = OpenAI(api_key=settings.openai_api_key)

    def verify(
        self,
        claim: Claim,
        evidence: Sequence[Evidence],
    ) -> VerificationDecision:
        return self.verify_with_analysis(
            claim=claim,
            evidence=evidence,
            analysis=None,
        )

    def verify_with_analysis(
        self,
        claim: Claim,
        evidence: Sequence[Evidence],
        analysis: InvestigationAnalysis | None,
    ) -> VerificationDecision:
        evidence_text = "\n\n".join(
            self._format_evidence(item)
            for item in evidence
        )

        analysis_text = self._format_analysis(analysis)

        response = self.client.responses.parse(
            model="gpt-5.6-terra",
            input=[
                {
                    "role": "system",
                    "content": (
                        "You are an evidence verification engine. "
                        "Evaluate the claim only against the supplied evidence. "
                        "Do not use outside knowledge. "
                        "Determine whether the evidence supports, contradicts, "
                        "or leaves the claim inconclusive. "
                        "Cite only evidence IDs that were supplied. "
                        "Treat evidence quality scores as supporting signals, "
                        "not proof of truth. "
                        "Do not automatically trust official sources. "
                        "Do not treat evidence with unknown timestamps as "
                        "historically verified. "
                        "Consider detected contradictions, but independently "
                        "assess the underlying evidence. "
                        "Use inconclusive when evidence is insufficient."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"CLAIM\n"
                        f"Text: {claim.text}\n"
                        f"Scope: {claim.scope or 'Not specified'}\n"
                        f"As of: {claim.as_of.isoformat()}\n\n"
                        f"STRUCTURED EVIDENCE ANALYSIS\n"
                        f"{analysis_text}\n\n"
                        f"EVIDENCE\n"
                        f"{evidence_text}"
                    ),
                },
            ],
            text_format=VerificationDecision,
        )

        if response.output_parsed is None:
            raise RuntimeError(
                "LLM returned no structured verification decision"
            )

        return response.output_parsed

    @staticmethod
    def _format_analysis(
        analysis: InvestigationAnalysis | None,
    ) -> str:
        if analysis is None:
            return "No structured evidence analysis was supplied."

        lines = ["EVIDENCE QUALITY"]

        for item in analysis.evidence_analysis:
            quality = item.quality

            lines.append(
                f"""
Evidence ID: {item.evidence_id}
Authority score: {quality.authority_score}
Freshness score: {quality.freshness_score}
Temporal validity: {quality.temporal_valid}
Completeness score: {quality.completeness_score}
""".strip()
            )

        lines.append("\nDETECTED CONTRADICTIONS")

        if not analysis.contradictions:
            lines.append("No numeric contradictions detected.")
        else:
            for contradiction in analysis.contradictions:
                lines.append(
                    f"""
Evidence A ID: {contradiction.evidence_a_id}
Evidence B ID: {contradiction.evidence_b_id}
Conflict type: {contradiction.conflict_type}
Values A: {contradiction.values_a}
Values B: {contradiction.values_b}
""".strip()
                )

        return "\n".join(lines)

    @staticmethod
    def _format_evidence(evidence: Evidence) -> str:
        return (
            f"Evidence ID: {evidence.id}\n"
            f"Source type: {evidence.source_type}\n"
            f"Title: {evidence.title or 'Untitled'}\n"
            f"Content: {evidence.content}\n"
            f"Source URL: {evidence.source_url or 'Not provided'}\n"
            f"Published at: "
            f"{evidence.published_at.isoformat() if evidence.published_at else 'Not provided'}\n"
            f"Observed at: "
            f"{evidence.observed_at.isoformat() if evidence.observed_at else 'Not provided'}\n"
            f"Authority: {evidence.authority or 'Not specified'}"
        )
