from collections.abc import Sequence

from google import genai

from backend.app.core.config import settings
from backend.app.models.claim import Claim
from backend.app.models.evidence import Evidence
from backend.app.schemas.verification import VerificationDecision
from backend.app.services.evidence_verifier import EvidenceVerifier


class GeminiVerifier(EvidenceVerifier):
    def __init__(self) -> None:
        self.client = genai.Client(api_key=settings.gemini_api_key)

    def verify(
        self,
        claim: Claim,
        evidence: Sequence[Evidence],
    ) -> VerificationDecision:
        evidence_text = "\n\n".join(
            self._format_evidence(item)
            for item in evidence
        )

        prompt = f"""
You are TraceLedger, an evidence verification engine.

Evaluate the claim ONLY against the supplied evidence.

Rules:
1. Do not use outside knowledge.
2. Do not invent facts or evidence.
3. The claim must be classified as supported, contradicted, or inconclusive.
4. SUPPORTED means the supplied evidence directly supports the claim.
5. CONTRADICTED means the supplied evidence directly conflicts with the claim.
6. INCONCLUSIVE means the supplied evidence is insufficient to establish either.
7. Cite only evidence IDs that appear in the supplied evidence.
8. Explain the reasoning using the actual evidence.
9. Consider the claim's scope and "as of" timestamp.
10. If the evidence conflicts with the claim, explicitly explain the conflict.

CLAIM
Text: {claim.text}
Scope: {claim.scope or "Not specified"}
As of: {claim.as_of.isoformat()}

EVIDENCE
{evidence_text}
"""

        interaction = self.client.interactions.create(
            model="gemini-3.6-flash",
            input=prompt,
            response_format={
                "type": "text",
                "mime_type": "application/json",
                "schema": VerificationDecision.model_json_schema(),
            },
        )

        if not interaction.output_text:
            raise RuntimeError(
                "Gemini returned no structured verification decision"
            )

        return VerificationDecision.model_validate_json(
            interaction.output_text
        )

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