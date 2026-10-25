from dataclasses import dataclass
from datetime import datetime, timezone

from backend.app.models.evidence import Evidence


@dataclass(frozen=True)
class EvidenceQuality:
    authority_score: float
    freshness_score: float
    temporal_valid: bool
    completeness_score: float


class EvidenceQualityService:
    AUTHORITY_SCORES = {
        "official": 1.0,
        "primary": 1.0,
        "internal": 0.9,
        "verified": 0.8,
        "secondary": 0.6,
        "unknown": 0.3,
    }

    def evaluate(
        self,
        evidence: Evidence,
        *,
        as_of: datetime,
    ) -> EvidenceQuality:
        return EvidenceQuality(
            authority_score=self._authority_score(evidence),
            freshness_score=self._freshness_score(evidence, as_of),
            temporal_valid=self._is_temporally_valid(evidence, as_of),
            completeness_score=self._completeness_score(evidence),
        )

    def _authority_score(self, evidence: Evidence) -> float:
        authority = (evidence.authority or "unknown").strip().lower()
        return self.AUTHORITY_SCORES.get(authority, 0.3)

    def _freshness_score(
        self,
        evidence: Evidence,
        as_of: datetime,
    ) -> float:
        reference_time = evidence.observed_at or evidence.published_at

        if reference_time is None:
            return 0.0

        if reference_time > as_of:
            return 0.0

        if reference_time.tzinfo is None:
            reference_time = reference_time.replace(tzinfo=timezone.utc)

        if as_of.tzinfo is None:
            as_of = as_of.replace(tzinfo=timezone.utc)

        age_days = max(
            0,
            (as_of - reference_time).days,
        )

        if age_days <= 30:
            return 1.0

        if age_days <= 180:
            return 0.8

        if age_days <= 365:
            return 0.6

        if age_days <= 730:
            return 0.4

        return 0.2

    def _is_temporally_valid(
        self,
        evidence: Evidence,
        as_of: datetime,
    ) -> bool:
        if evidence.observed_at is not None:
            return evidence.observed_at <= as_of

        if evidence.published_at is not None:
            return evidence.published_at <= as_of

        return False

    def _completeness_score(self, evidence: Evidence) -> float:
        title_score = 1.0 if evidence.title and evidence.title.strip() else 0.0

        content_length = len((evidence.content or "").strip())

        if content_length >= 500:
            content_score = 1.0
        elif content_length >= 200:
            content_score = 0.8
        elif content_length >= 50:
            content_score = 0.5
        elif content_length > 0:
            content_score = 0.2
        else:
            content_score = 0.0

        return (title_score + content_score) / 2