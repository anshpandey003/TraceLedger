
from typing import TypedDict
from uuid import UUID

from langgraph.graph import END, START, StateGraph
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.enums import ClaimStatus, InvestigationStatus
from backend.app.models.claim import Claim
from backend.app.models.contradiction import Contradiction
from backend.app.models.evidence_analysis import EvidenceAnalysis
from backend.app.models.investigation import Investigation
from backend.app.models.investigation_result import InvestigationResult
from backend.app.models.result_citation import ResultCitation
from backend.app.retrieval.postgres import PostgreSQLEvidenceRetriever
from backend.app.services.evidence_verifier import EvidenceVerifier
from backend.app.services.investigation_analysis import (
    InvestigationAnalysis,
    InvestigationAnalysisService,
)
from backend.app.services.verification_validator import VerificationValidator


class ClaimWorkflowState(TypedDict, total=False):
    claim: Claim
    evidence: list
    analysis: InvestigationAnalysis
    decision: object
    result: InvestigationResult


class InvestigationService:
    def __init__(
        self,
        db: Session,
        verifier: EvidenceVerifier,
        retriever: PostgreSQLEvidenceRetriever,
        analysis_service: InvestigationAnalysisService | None = None,
    ) -> None:
        self.db = db
        self.verifier = verifier
        self.retriever = retriever
        self.analysis_service = (
            analysis_service or InvestigationAnalysisService()
        )
        self.graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(ClaimWorkflowState)

        workflow.add_node("retrieve", self._retrieve_evidence)
        workflow.add_node("analyze", self._analyze_evidence)
        workflow.add_node("verify", self._verify_claim)
        workflow.add_node("persist_result", self._persist_result)
        workflow.add_node("persist_inconclusive", self._persist_inconclusive)

        workflow.add_edge(START, "retrieve")
        workflow.add_conditional_edges(
            "retrieve",
            self._route_after_retrieval,
            {
                "analyze": "analyze",
                "persist_inconclusive": "persist_inconclusive",
            },
        )
        workflow.add_edge("analyze", "verify")
        workflow.add_edge("verify", "persist_result")
        workflow.add_edge("persist_result", END)
        workflow.add_edge("persist_inconclusive", END)

        return workflow.compile()

    def run(self, investigation_id: UUID) -> Investigation:
        investigation = self.db.get(Investigation, investigation_id)

        if investigation is None:
            raise ValueError("Investigation not found")

        investigation.status = InvestigationStatus.RUNNING
        self.db.flush()

        try:
            claims = list(
                self.db.scalars(
                    select(Claim)
                    .where(Claim.investigation_id == investigation_id)
                    .order_by(Claim.created_at)
                ).all()
            )

            for claim in claims:
                self._process_claim(claim)

            investigation.status = InvestigationStatus.COMPLETED
            self.db.commit()
            self.db.refresh(investigation)
            return investigation

        except Exception:
            self.db.rollback()

            investigation = self.db.get(Investigation, investigation_id)
            if investigation is not None:
                investigation.status = InvestigationStatus.FAILED
                self.db.commit()
                self.db.refresh(investigation)

            raise

    def _process_claim(self, claim: Claim) -> None:
        existing_result = self.db.scalar(
            select(InvestigationResult).where(
                InvestigationResult.claim_id == claim.id
            )
        )

        if existing_result is not None:
            claim.status = ClaimStatus.COMPLETED
            return

        claim.status = ClaimStatus.INVESTIGATING
        self.graph.invoke({"claim": claim})

    def _retrieve_evidence(self, state: ClaimWorkflowState) -> dict:
        claim = state["claim"]

        retrieval_results = self.retriever.retrieve_hybrid(
            claim_id=claim.id,
            query=claim.text,
            as_of=claim.as_of,
            limit=10,
        )

        return {
            "evidence": [item.evidence for item in retrieval_results]
        }

    @staticmethod
    def _route_after_retrieval(state: ClaimWorkflowState) -> str:
        return "analyze" if state.get("evidence") else "persist_inconclusive"

    def _analyze_evidence(self, state: ClaimWorkflowState) -> dict:
        claim = state["claim"]
        analysis = self.analysis_service.analyze(
            state["evidence"],
            as_of=claim.as_of,
        )
        return {"analysis": analysis}

    def _verify_claim(self, state: ClaimWorkflowState) -> dict:
        decision = self.verifier.verify(
            claim=state["claim"],
            evidence=state["evidence"],
        )
        decision = VerificationValidator.validate(
            decision=decision,
            evidence=state["evidence"],
        )
        return {"decision": decision}

    def _persist_result(self, state: ClaimWorkflowState) -> dict:
        claim = state["claim"]
        evidence = state["evidence"]
        analysis = state["analysis"]
        decision = state["decision"]

        result = InvestigationResult(
            claim_id=claim.id,
            verdict=decision.verdict,
            explanation=decision.explanation,
            confidence=decision.confidence,
        )
        self.db.add(result)
        self.db.flush()

        self._persist_analysis(result=result, analysis=analysis)

        cited_evidence_ids = set(decision.evidence_ids)
        for evidence_item in evidence:
            if evidence_item.id in cited_evidence_ids:
                self.db.add(
                    ResultCitation(
                        result_id=result.id,
                        evidence_id=evidence_item.id,
                    )
                )

        claim.status = ClaimStatus.COMPLETED
        return {"result": result}

    def _persist_inconclusive(self, state: ClaimWorkflowState) -> dict:
        claim = state["claim"]

        result = InvestigationResult(
            claim_id=claim.id,
            verdict="inconclusive",
            explanation=(
                "No relevant evidence is available for "
                "this claim at the specified point in time."
            ),
            confidence=0.0,
        )
        self.db.add(result)
        claim.status = ClaimStatus.COMPLETED
        return {"result": result}

    def _persist_analysis(
        self,
        result: InvestigationResult,
        analysis: InvestigationAnalysis,
    ) -> None:
        for evidence_analysis in analysis.evidence_analysis:
            quality = evidence_analysis.quality
            self.db.add(
                EvidenceAnalysis(
                    result_id=result.id,
                    evidence_id=evidence_analysis.evidence_id,
                    authority_score=quality.authority_score,
                    freshness_score=quality.freshness_score,
                    temporal_valid=quality.temporal_valid,
                    completeness_score=quality.completeness_score,
                )
            )

        for contradiction in analysis.contradictions:
            self.db.add(
                Contradiction(
                    result_id=result.id,
                    evidence_a_id=contradiction.evidence_a_id,
                    evidence_b_id=contradiction.evidence_b_id,
                    conflict_type=contradiction.conflict_type,
                    values_a=[
                        self._serialize_assertion(value)
                        for value in contradiction.values_a
                    ],
                    values_b=[
                        self._serialize_assertion(value)
                        for value in contradiction.values_b
                    ],
                )
            )

    @staticmethod
    def _serialize_assertion(assertion) -> dict:
        return {
            "assertion_type": assertion.assertion_type,
            "raw_text": assertion.fact.raw_text,
            "value": assertion.fact.value,
            "unit": assertion.fact.unit,
        }
