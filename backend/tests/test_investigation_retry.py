
from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import uuid4

from backend.app.schemas.verification import VerificationDecision
from backend.app.services.investigation_analysis import (
    InvestigationAnalysis,
)
from backend.app.services.investigation_service import InvestigationService


class FakeSession:
    def __init__(self):
        self.added = []

    def add(self, instance):
        self.added.append(instance)

    def flush(self):
        pass


class FakeRetriever:
    def __init__(self, responses):
        self.responses = list(responses)
        self.queries = []

    def retrieve_hybrid(
        self,
        *,
        claim_id,
        query,
        as_of,
        limit,
    ):
        self.queries.append(query)
        return self.responses.pop(0)


class FakeQueryRewriter:
    def __init__(self):
        self.rewrite = MagicMock(
            return_value="refund API maximum transaction limit"
        )


class FakeAnalysisService:
    def analyze(self, evidence, *, as_of):
        return InvestigationAnalysis(
            evidence_analysis=(),
            contradictions=(),
        )


class FakeVerifier:
    def __init__(self):
        self.verify_calls = []

    def verify(self, *, claim, evidence):
        self.verify_calls.append((claim, evidence))

        return VerificationDecision(
            verdict="supported",
            explanation="The supplied evidence supports the claim.",
            confidence=0.95,
            evidence_ids=[evidence[0].id],
        )


def make_claim():
    return MagicMock(
        id=uuid4(),
        text="The refund API supports refunds up to Rs 50,000",
        scope="Production refund API",
        as_of=datetime(2026, 9, 22, tzinfo=timezone.utc),
        status=None,
    )


def make_retrieval_result():
    evidence = MagicMock(id=uuid4())

    return MagicMock(
        evidence=evidence,
        score=0.9,
        source="hybrid",
        rank=1,
    )


def make_service(responses):
    db = FakeSession()
    retriever = FakeRetriever(responses)
    rewriter = FakeQueryRewriter()
    verifier = FakeVerifier()

    service = InvestigationService(
        db=db,
        verifier=verifier,
        retriever=retriever,
        analysis_service=FakeAnalysisService(),
        query_rewriter=rewriter,
    )

    return service, db, retriever, rewriter, verifier


def test_initial_retrieval_success_skips_query_rewriting():
    claim = make_claim()
    evidence_result = make_retrieval_result()

    service, db, retriever, rewriter, verifier = make_service(
        [[evidence_result]]
    )

    result = service.graph.invoke({"claim": claim})

    assert retriever.queries == [claim.text]
    rewriter.rewrite.assert_not_called()
    assert len(verifier.verify_calls) == 1
    assert result["result"].verdict == "supported"


def test_empty_initial_retrieval_triggers_rewritten_retry():
    claim = make_claim()
    evidence_result = make_retrieval_result()

    service, db, retriever, rewriter, verifier = make_service(
        [
            [],
            [evidence_result],
        ]
    )

    result = service.graph.invoke({"claim": claim})

    assert retriever.queries == [
        claim.text,
        "refund API maximum transaction limit",
    ]

    rewriter.rewrite.assert_called_once_with(claim.text)
    assert len(verifier.verify_calls) == 1
    assert result["result"].verdict == "supported"


def test_empty_initial_and_retry_retrieval_persist_inconclusive():
    claim = make_claim()

    service, db, retriever, rewriter, verifier = make_service(
        [
            [],
            [],
        ]
    )

    result = service.graph.invoke({"claim": claim})

    assert retriever.queries == [
        claim.text,
        "refund API maximum transaction limit",
    ]

    rewriter.rewrite.assert_called_once_with(claim.text)
    assert verifier.verify_calls == []

    assert result["result"].verdict == "inconclusive"
    assert result["result"].confidence == 0.0

    assert "one reformulated retrieval attempt" in (
        result["result"].explanation
    )

    assert claim.status is not None
