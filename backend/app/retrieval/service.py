from abc import ABC, abstractmethod
from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

from backend.app.models.evidence import Evidence


class EvidenceRetriever(ABC):
    @abstractmethod
    def retrieve(
        self,
        claim_id: UUID,
        query: str,
        *,
        as_of: datetime,
        limit: int = 10,
    ) -> Sequence[Evidence]:
        """Retrieve evidence relevant to a claim and its point in time."""
        raise NotImplementedError