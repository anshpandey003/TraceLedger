from collections.abc import Sequence
from uuid import UUID

from backend.app.models.evidence import Evidence
from backend.app.schemas.verification import VerificationDecision


class VerificationValidator:
    @staticmethod
    def validate(
        decision: VerificationDecision,
        evidence: Sequence[Evidence],
    ) -> VerificationDecision:
        available_evidence_ids: set[UUID] = {
            evidence_item.id for evidence_item in evidence
        }

        invalid_evidence_ids = [
            evidence_id
            for evidence_id in decision.evidence_ids
            if evidence_id not in available_evidence_ids
        ]

        if invalid_evidence_ids:
            raise ValueError(
                "Verification decision contains evidence IDs "
                "that were not supplied to the verifier: "
                f"{invalid_evidence_ids}"
            )

        return decision