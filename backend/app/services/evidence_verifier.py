from abc import ABC, abstractmethod
from collections.abc import Sequence

from backend.app.models.claim import Claim
from backend.app.models.evidence import Evidence
from backend.app.schemas.verification import VerificationDecision


class EvidenceVerifier(ABC):
    @abstractmethod
    def verify(
        self,
        claim: Claim,
        evidence: Sequence[Evidence],
    ) -> VerificationDecision:
        """Evaluate a claim against the provided evidence."""
        raise NotImplementedError