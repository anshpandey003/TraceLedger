from uuid import uuid4

from backend.app.core.enums import Verdict
from backend.app.models.investigation_result import InvestigationResult
from backend.app.services.assertion_extractor import NumericAssertion
from backend.app.services.fact_normalizer import NumericFact
from backend.app.services.investigation_analysis import (
    EvidenceAnalysis,
    InvestigationAnalysis,
)
from backend.app.services.investigation_service import InvestigationService
from backend.app.services.contradiction_detector import Contradiction
from backend.app.services.evidence_quality import EvidenceQuality


class FakeSession:
    def __init__(self) -> None:
        self.added = []

    def add(self, instance) -> None:
        self.added.append(instance)


def test_persist_analysis_creates_quality_and_contradiction_rows():
    db = FakeSession()

    service = InvestigationService(
        db=db,
        verifier=None,
        retriever=None,
    )

    result = InvestigationResult(
        id=uuid4(),
        claim_id=uuid4(),
        verdict=Verdict.CONTRADICTED,
        explanation="The evidence contains conflicting refund limits.",
        confidence=0.95,
    )

    evidence_a_id = uuid4()
    evidence_b_id = uuid4()

    quality_a = EvidenceQuality(
        authority_score=1.0,
        freshness_score=0.8,
        temporal_valid=True,
        completeness_score=0.9,
    )

    quality_b = EvidenceQuality(
        authority_score=0.6,
        freshness_score=0.4,
        temporal_valid=True,
        completeness_score=0.7,
    )

    evidence_analysis = (
        EvidenceAnalysis(
            evidence_id=evidence_a_id,
            quality=quality_a,
        ),
        EvidenceAnalysis(
            evidence_id=evidence_b_id,
            quality=quality_b,
        ),
    )

    assertion_a = NumericAssertion(
        fact=NumericFact(
            value=25000.0,
            unit=None,
            raw_text="₹25,000",
        ),
        assertion_type="maximum",
    )

    assertion_b = NumericAssertion(
        fact=NumericFact(
            value=50000.0,
            unit=None,
            raw_text="₹50,000",
        ),
        assertion_type="maximum",
    )

    contradiction = Contradiction(
        evidence_a_id=evidence_a_id,
        evidence_b_id=evidence_b_id,
        conflict_type="numeric_value",
        values_a=(assertion_a,),
        values_b=(assertion_b,),
    )

    analysis = InvestigationAnalysis(
        evidence_analysis=evidence_analysis,
        contradictions=(contradiction,),
    )

    service._persist_analysis(
        result=result,
        analysis=analysis,
    )

    assert len(db.added) == 3

    persisted_quality_a = db.added[0]
    persisted_quality_b = db.added[1]
    persisted_contradiction = db.added[2]

    assert persisted_quality_a.result_id == result.id
    assert persisted_quality_a.evidence_id == evidence_a_id
    assert persisted_quality_a.authority_score == 1.0
    assert persisted_quality_a.freshness_score == 0.8
    assert persisted_quality_a.temporal_valid is True
    assert persisted_quality_a.completeness_score == 0.9

    assert persisted_quality_b.result_id == result.id
    assert persisted_quality_b.evidence_id == evidence_b_id
    assert persisted_quality_b.authority_score == 0.6
    assert persisted_quality_b.freshness_score == 0.4
    assert persisted_quality_b.temporal_valid is True
    assert persisted_quality_b.completeness_score == 0.7

    assert persisted_contradiction.result_id == result.id
    assert persisted_contradiction.evidence_a_id == evidence_a_id
    assert persisted_contradiction.evidence_b_id == evidence_b_id
    assert persisted_contradiction.conflict_type == "numeric_value"

    assert persisted_contradiction.values_a == [
        {
            "assertion_type": "maximum",
            "raw_text": "₹25,000",
            "value": 25000.0,
            "unit": None,
        }
    ]

    assert persisted_contradiction.values_b == [
        {
            "assertion_type": "maximum",
            "raw_text": "₹50,000",
            "value": 50000.0,
            "unit": None,
        }
    ]