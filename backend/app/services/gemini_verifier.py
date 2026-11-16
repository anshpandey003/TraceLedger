
from collections.abc import Sequence

from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from backend.app.core.config import settings
from backend.app.models.claim import Claim
from backend.app.models.evidence import Evidence
from backend.app.schemas.verification import VerificationDecision
from backend.app.services.evidence_verifier import EvidenceVerifier
from backend.app.services.investigation_analysis import InvestigationAnalysis


class GeminiVerifier(EvidenceVerifier):
    def __init__(self) -> None:
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-3.6-flash",
            google_api_key=settings.gemini_api_key,
            temperature=0,
        )

        self.prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """
You are TraceLedger, an evidence verification engine.

Evaluate the claim ONLY against the supplied evidence and its
structured analysis.

Rules:
1. Do not use outside knowledge.
2. Do not invent facts or evidence.
3. Classify the claim as supported, contradicted, or inconclusive.
4. SUPPORTED means the supplied evidence directly supports the claim.
5. CONTRADICTED means the supplied evidence directly conflicts with the claim.
6. INCONCLUSIVE means the supplied evidence is insufficient to establish either.
7. Cite only evidence IDs that appear in the supplied evidence.
8. Explain the reasoning using the actual evidence.
9. Consider the claim's scope and as-of timestamp.
10. Explicitly explain conflicts between evidence and the claim.
11. Treat authority, freshness, temporal validity, and completeness scores
    as supporting signals, NOT as proof.
12. Do not automatically trust evidence because it is labelled official.
13. Evidence with unknown timestamps must not be represented as
    historically verified.
14. Independently assess underlying evidence before deciding the verdict.
15. If evidence is insufficient or temporally unreliable, use inconclusive.
                    """,
                ),
                (
                    "human",
                    """
CLAIM
Text: {claim_text}
Scope: {claim_scope}
As of: {claim_as_of}

STRUCTURED EVIDENCE ANALYSIS
{analysis_text}

EVIDENCE
{evidence_text}
                    """,
                ),
            ]
        )

        self.chain = (
            self.prompt
            | self.llm.with_structured_output(VerificationDecision)
        )

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
        if not evidence:
            raise ValueError(
                "At least one evidence item is required for verification"
            )

        decision = self.chain.invoke(
            {
                "claim_text": claim.text,
                "claim_scope": claim.scope or "Not specified",
                "claim_as_of": claim.as_of.isoformat(),
                "analysis_text": self._format_analysis(analysis),
                "evidence_text": "\n\n".join(
                    self._format_evidence(item)
                    for item in evidence
                ),
            }
        )

        if decision is None:
            raise RuntimeError(
                "Gemini returned no structured verification decision"
            )

        return decision

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
