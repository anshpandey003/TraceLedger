from __future__ import annotations

import json
import statistics
import time
from typing import Any
from uuid import UUID, uuid4

from backend.app.db.session import SessionLocal
from backend.app.evaluation.dataset import load_dataset
from backend.app.evaluation.metrics import (
    mean_reciprocal_rank,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
)
from backend.app.models.claim import Claim
from backend.app.models.evidence import Evidence
from backend.app.models.investigation import Investigation
from backend.app.retrieval.postgres import PostgreSQLEvidenceRetriever
from backend.app.services.reranker import FlashRankReranker


K = 5
RRF_K = 60
RERANK_CANDIDATE_LIMIT = 20

STRATEGIES = (
    "vector",
    "lexical",
    "hybrid",
    "hybrid_reranked",
    "hybrid_fused",
    "hybrid_weighted_025",
    "hybrid_weighted_050",
    "hybrid_weighted_075",
)

THRESHOLD_VALUES = (0.30, 0.35, 0.40, 0.45)


def _retrieved_external_ids(
    results: list[Any],
    external_id_by_uuid: dict[UUID, str],
) -> list[str]:
    return [
        external_id_by_uuid[result.evidence.id]
        for result in results
        if result.evidence.id in external_id_by_uuid
    ]


def _fuse_hybrid_and_reranker(
    hybrid_candidates: list[Any],
    reranked_candidates: list[Any],
    *,
    rrf_k: int = RRF_K,
    hybrid_weight: float = 0.5,
) -> tuple[list[Any], dict[str, dict[str, float]]]:
    """Fuse original hybrid ranks and cross-encoder ranks using RRF.

    Both input lists must contain the complete candidate pool.
    Original hybrid ranks are preserved from the retrieval results.
    Cross-encoder ranks come from the reranked results.
    """

    if not 0.0 <= hybrid_weight <= 1.0:
        raise ValueError("hybrid_weight must be between 0 and 1")

    if rrf_k <= 0:
        raise ValueError("rrf_k must be greater than zero")

    if not hybrid_candidates or not reranked_candidates:
        return [], {}

    hybrid_by_id = {
        str(result.evidence.id): result
        for result in hybrid_candidates
    }

    rerank_rank_by_id = {
        str(result.evidence.id): result.rank
        for result in reranked_candidates
    }

    fused_entries = []

    for evidence_id, original in hybrid_by_id.items():
        hybrid_rank = original.rank
        rerank_rank = rerank_rank_by_id.get(evidence_id)

        # Only candidates present in both rankings can be fused.
        if hybrid_rank is None or rerank_rank is None:
            continue

        fusion_score = (
            hybrid_weight / (rrf_k + hybrid_rank)
            + (1.0 - hybrid_weight) / (rrf_k + rerank_rank)
        )

        fused_entries.append(
            (
                original,
                fusion_score,
                hybrid_rank,
                rerank_rank,
                evidence_id,
            )
        )

    fused_entries.sort(
        key=lambda entry: (
            -entry[1],
            entry[2],
            entry[3],
            entry[4],
        )
    )

    fused_results = [entry[0] for entry in fused_entries]

    diagnostics = {
        entry[4]: {
            "hybrid_rank": float(entry[2]),
            "reranker_rank": float(entry[3]),
            "fusion_score": entry[1],
        }
        for entry in fused_entries
    }

    return fused_results, diagnostics


def _calculate_metrics(
    rankings: list[list[str]],
    relevant_sets: list[set[str]],
    relevance_maps: list[dict[str, float]],
    k: int,
) -> dict[str, float]:
    if not rankings:
        return {
            f"precision@{k}": 0.0,
            f"recall@{k}": 0.0,
            "mrr": 0.0,
            f"ndcg@{k}": 0.0,
        }

    return {
        f"precision@{k}": sum(
            precision_at_k(ranking, relevant, k)
            for ranking, relevant in zip(rankings, relevant_sets)
        ) / len(rankings),
        f"recall@{k}": sum(
            recall_at_k(ranking, relevant, k)
            for ranking, relevant in zip(rankings, relevant_sets)
        ) / len(rankings),
        "mrr": mean_reciprocal_rank(rankings, relevant_sets),
        f"ndcg@{k}": sum(
            ndcg_at_k(ranking, relevance, k)
            for ranking, relevance in zip(rankings, relevance_maps)
        ) / len(rankings),
    }


def _average(values: list[float]) -> float:
    return statistics.mean(values) if values else 0.0


def _print_report(
    aggregate: dict[str, dict[str, float]],
    per_case: dict[str, dict[str, Any]],
    latency: dict[str, Any],
    k: int,
) -> None:
    metric_names = list(next(iter(aggregate.values())).keys())

    print("\n" + "=" * 110)
    print("TRACELEDGER SHARED-CORPUS RETRIEVAL BENCHMARK")
    print("=" * 110)

    print("\nAGGREGATE RETRIEVAL QUALITY")
    print("-" * 110)
    print(
        f"{'Strategy':<22}"
        + "".join(f"{metric:>15}" for metric in metric_names)
    )

    for strategy, metrics in aggregate.items():
        print(
            f"{strategy:<22}"
            + "".join(
                f"{metrics[metric]:>15.4f}"
                for metric in metric_names
            )
        )

    print("\nLATENCY BREAKDOWN (milliseconds)")
    print("-" * 110)
    print(
        f"{'Measurement':<30}"
        f"{'Mean':>15}"
        f"{'Median':>15}"
        f"{'P95':>15}"
    )

    for name, values in latency.items():
        print(
            f"{name:<30}"
            f"{values['mean_ms']:>15.2f}"
            f"{values['median_ms']:>15.2f}"
            f"{values['p95_ms']:>15.2f}"
        )

    print("\nPER-CASE RESULTS")
    print("-" * 110)

    for case_id, details in per_case.items():
        print(f"\n{case_id} | {details['claim']}")
        print(f"  Relevant evidence: {details['relevant_ids']}")

        for strategy in STRATEGIES:
            metrics = details["metrics"][strategy]
            retrieved = details["retrieved_ids"][strategy]
            elapsed = details["latency_ms"][strategy]

            formatted = " | ".join(
                f"{name}: {value:.4f}"
                for name, value in metrics.items()
            )

            print(f"  {strategy:<20} {formatted}")
            print(f"                       Retrieved: {retrieved}")
            print(f"                       Latency: {elapsed:.2f} ms")

    print("\n" + "=" * 110)


def _latency_summary(samples: list[float]) -> dict[str, float]:
    if not samples:
        return {
            "mean_ms": 0.0,
            "median_ms": 0.0,
            "p95_ms": 0.0,
        }

    ordered = sorted(samples)

    p95_index = min(
        len(ordered) - 1,
        max(0, int(0.95 * len(ordered) + 0.999) - 1),
    )

    return {
        "mean_ms": _average(samples),
        "median_ms": statistics.median(samples),
        "p95_ms": ordered[p95_index],
    }


def _run_threshold_sensitivity(
    retriever: PostgreSQLEvidenceRetriever,
    cases: list[Any],
    evidence_ids: set[UUID],
    external_id_by_uuid: dict[UUID, str],
    relevant_sets: list[set[str]],
    relevance_maps: list[dict[str, float]],
    k: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Evaluate vector and hybrid retrieval across distance thresholds."""

    original_threshold = retriever.similarity_threshold

    sensitivity_results: dict[str, Any] = {}
    sensitivity_latency: dict[str, Any] = {}

    retrieval_methods = {
        "vector": retriever.retrieve_vector_corpus,
        "hybrid": retriever.retrieve_hybrid_corpus,
    }

    try:
        for threshold in THRESHOLD_VALUES:
            retriever.similarity_threshold = threshold

            rankings: dict[str, list[list[str]]] = {
                strategy: [] for strategy in retrieval_methods
            }

            latency_samples: dict[str, list[float]] = {
                strategy: [] for strategy in retrieval_methods
            }

            for case in cases:
                for strategy, retrieve in retrieval_methods.items():
                    started = time.perf_counter()

                    results = retrieve(
                        query=case.claim,
                        as_of=case.as_of,
                        evidence_ids=evidence_ids,
                        limit=k,
                    )

                    elapsed_ms = (
                        time.perf_counter() - started
                    ) * 1000

                    latency_samples[strategy].append(elapsed_ms)

                    rankings[strategy].append(
                        _retrieved_external_ids(
                            results,
                            external_id_by_uuid,
                        )
                    )

            threshold_key = f"{threshold:.2f}"

            sensitivity_results[threshold_key] = {
                strategy: _calculate_metrics(
                    rankings[strategy],
                    relevant_sets,
                    relevance_maps,
                    k,
                )
                for strategy in retrieval_methods
            }

            sensitivity_latency[threshold_key] = {
                strategy: _latency_summary(
                    latency_samples[strategy]
                )
                for strategy in retrieval_methods
            }

    finally:
        retriever.similarity_threshold = original_threshold

    return sensitivity_results, sensitivity_latency


def _print_threshold_report(
    sensitivity: dict[str, Any],
    latency: dict[str, Any],
    k: int,
) -> None:
    print("\nTHRESHOLD SENSITIVITY")
    print("=" * 100)

    print(
        f"{'Threshold':<12}"
        f"{'Strategy':<10}"
        f"{'Precision@' + str(k):>14}"
        f"{'Recall@' + str(k):>12}"
        f"{'MRR':>10}"
        f"{'NDCG@' + str(k):>12}"
        f"{'Mean ms':>12}"
    )

    for threshold, strategies in sensitivity.items():
        for strategy, metrics in strategies.items():
            mean_latency = latency[threshold][strategy]["mean_ms"]

            print(
                f"{threshold:<12}"
                f"{strategy:<10}"
                f"{metrics[f'precision@{k}']:>14.4f}"
                f"{metrics[f'recall@{k}']:>12.4f}"
                f"{metrics['mrr']:>10.4f}"
                f"{metrics[f'ndcg@{k}']:>12.4f}"
                f"{mean_latency:>12.2f}"
            )

    print("=" * 100)


def run_benchmark(k: int = K) -> dict[str, Any]:
    if k <= 0:
        raise ValueError("k must be greater than zero")

    cases = load_dataset()

    if not cases:
        raise ValueError("Evaluation dataset contains no cases.")

    session = SessionLocal()
    investigation_id = uuid4()

    try:
        investigation = Investigation(
            id=investigation_id,
            title="Temporary Shared-Corpus Evaluation",
            description="Temporary synthetic benchmark records.",
        )

        session.add(investigation)
        session.flush()

        retriever = PostgreSQLEvidenceRetriever(session)
        reranker = FlashRankReranker(
            model_name="ms-marco-MiniLM-L-12-v2"
        )

        external_id_by_uuid: dict[UUID, str] = {}

        # Generate document embeddings and insert temporary records.
        document_embedding_times: list[float] = []

        for case in cases:
            claim = Claim(
                id=uuid4(),
                investigation_id=investigation_id,
                text=case.claim,
                as_of=case.as_of,
            )

            session.add(claim)

            for item in case.evidence:
                evidence_uuid = uuid4()

                embedding_started = time.perf_counter()

                embedding = retriever.embedding_service.embed_document(
                    title=item.title,
                    content=item.content,
                )

                document_embedding_times.append(
                    (time.perf_counter() - embedding_started) * 1000
                )

                session.add(
                    Evidence(
                        id=evidence_uuid,
                        claim_id=claim.id,
                        source_type=item.source_type,
                        title=item.title,
                        content=item.content,
                        published_at=item.published_at,
                        observed_at=item.observed_at,
                        authority=getattr(item, "authority", None)
                        or item.source_type,
                        embedding=embedding,
                    )
                )

                external_id_by_uuid[evidence_uuid] = item.id

        session.commit()

        evaluation_evidence_ids = set(external_id_by_uuid)

        # Precompute unique query embeddings before retrieval timing.
        query_embedding_times: list[float] = []
        precomputed_query_embeddings: dict[str, list[float]] = {}

        for case in cases:
            if case.claim in precomputed_query_embeddings:
                continue

            started = time.perf_counter()

            embedding = retriever.embedding_service.embed_query(
                case.claim
            )

            query_embedding_times.append(
                (time.perf_counter() - started) * 1000
            )

            precomputed_query_embeddings[case.claim] = embedding

        # Warm up the database query path.
        warmup_case = cases[0]

        retriever.retrieve_lexical_corpus(
            query=warmup_case.claim,
            as_of=warmup_case.as_of,
            evidence_ids=evaluation_evidence_ids,
            limit=k,
        )

        warmup_embedding = precomputed_query_embeddings[
            warmup_case.claim
        ]

        distance_expression = Evidence.embedding.cosine_distance(
            warmup_embedding
        )

        session.query(Evidence.id).filter(
            Evidence.id.in_(evaluation_evidence_ids),
            Evidence.embedding.is_not(None),
        ).order_by(distance_expression).limit(k).all()

        # Warm up hybrid retrieval and FlashRank separately.
        warmup_candidates = retriever.retrieve_hybrid_corpus(
            query=warmup_case.claim,
            as_of=warmup_case.as_of,
            evidence_ids=evaluation_evidence_ids,
            limit=RERANK_CANDIDATE_LIMIT,
        )

        reranker_warmup_started = time.perf_counter()

        reranker.rerank(
            warmup_case.claim,
            warmup_candidates,
            top_k=len(warmup_candidates),
        )

        reranker_warmup_ms = (
            time.perf_counter() - reranker_warmup_started
        ) * 1000

        retrieval_methods = {
            "vector": retriever.retrieve_vector_corpus,
            "lexical": retriever.retrieve_lexical_corpus,
            "hybrid": retriever.retrieve_hybrid_corpus,
        }

        rankings: dict[str, list[list[str]]] = {
            strategy: [] for strategy in STRATEGIES
        }

        relevant_sets: list[set[str]] = []
        relevance_maps: list[dict[str, float]] = []
        per_case: dict[str, dict[str, Any]] = {}

        retrieval_samples: dict[str, list[float]] = {
            strategy: [] for strategy in STRATEGIES
        }

        reranking_samples: list[float] = []
        fusion_samples: list[float] = []

        for case in cases:
            relevant = set(case.expected_relevant_evidence_ids)

            relevance = {
                item.id: float(item.relevance_grade)
                for item in case.evidence
            }

            relevant_sets.append(relevant)
            relevance_maps.append(relevance)

            per_case[case.case_id] = {
                "claim": case.claim,
                "relevant_ids": sorted(relevant),
                "metrics": {},
                "retrieved_ids": {},
                "latency_ms": {},
                "candidate_recall": {},
                "candidate_retrieved_ids": {},
                "fusion_diagnostics": {},
            }

            # Run the original three retrieval strategies unchanged.
            for strategy, retrieve in retrieval_methods.items():
                started = time.perf_counter()

                results = retrieve(
                    query=case.claim,
                    as_of=case.as_of,
                    evidence_ids=evaluation_evidence_ids,
                    limit=k,
                )

                elapsed_ms = (
                    time.perf_counter() - started
                ) * 1000

                retrieval_samples[strategy].append(elapsed_ms)

                ranked_ids = _retrieved_external_ids(
                    results,
                    external_id_by_uuid,
                )

                rankings[strategy].append(ranked_ids)

                per_case[case.case_id]["retrieved_ids"][strategy] = (
                    ranked_ids
                )

                per_case[case.case_id]["latency_ms"][strategy] = (
                    elapsed_ms
                )

                per_case[case.case_id]["metrics"][strategy] = {
                    f"precision@{k}": precision_at_k(
                        ranked_ids, relevant, k
                    ),
                    f"recall@{k}": recall_at_k(
                        ranked_ids, relevant, k
                    ),
                    "mrr": mean_reciprocal_rank(
                        [ranked_ids], [relevant]
                    ),
                    f"ndcg@{k}": ndcg_at_k(
                        ranked_ids, relevance, k
                    ),
                }

                # Candidate-recall diagnostics at depths 5, 10 and 20.
                diagnostic_results = retrieve(
                    query=case.claim,
                    as_of=case.as_of,
                    evidence_ids=evaluation_evidence_ids,
                    limit=RERANK_CANDIDATE_LIMIT,
                )

                diagnostic_ids = _retrieved_external_ids(
                    diagnostic_results,
                    external_id_by_uuid,
                )

                per_case[case.case_id]["candidate_retrieved_ids"][
                    strategy
                ] = diagnostic_ids

                per_case[case.case_id]["candidate_recall"][
                    strategy
                ] = {
                    f"recall@{depth}": recall_at_k(
                        diagnostic_ids, relevant, depth
                    )
                    for depth in (5, 10, 20)
                }

            # -----------------------------------------------------
            # Experimental strategies: hybrid + FlashRank.
            # -----------------------------------------------------

            reranked_started = time.perf_counter()

            # Retrieve the complete hybrid candidate pool.
            rerank_candidates = retriever.retrieve_hybrid_corpus(
                query=case.claim,
                as_of=case.as_of,
                evidence_ids=evaluation_evidence_ids,
                limit=RERANK_CANDIDATE_LIMIT,
            )

            # Rerank ALL candidates so fusion can use every rank.
            reranking_started = time.perf_counter()

            reranked_results = reranker.rerank(
                case.claim,
                rerank_candidates,
                top_k=len(rerank_candidates),
            )
            
            reranking_ms = (
                time.perf_counter() - reranking_started
            ) * 1000

            reranking_samples.append(reranking_ms)

            # Pure cross-encoder ranking: same ordering as before,
            # with only the first k results used for evaluation.
            reranked_top_k = reranked_results[:k]

            reranked_ids = _retrieved_external_ids(
                reranked_top_k,
                external_id_by_uuid,
            )

            reranked_total_ms = (
                time.perf_counter() - reranked_started
            ) * 1000

            retrieval_samples["hybrid_reranked"].append(
                reranked_total_ms
            )

            rankings["hybrid_reranked"].append(reranked_ids)

            per_case[case.case_id]["retrieved_ids"][
                "hybrid_reranked"
            ] = reranked_ids

            per_case[case.case_id]["latency_ms"][
                "hybrid_reranked"
            ] = reranked_total_ms

            per_case[case.case_id]["metrics"][
                "hybrid_reranked"
            ] = {
                f"precision@{k}": precision_at_k(
                    reranked_ids, relevant, k
                ),
                f"recall@{k}": recall_at_k(
                    reranked_ids, relevant, k
                ),
                "mrr": mean_reciprocal_rank(
                    [reranked_ids], [relevant]
                ),
                f"ndcg@{k}": ndcg_at_k(
                    reranked_ids, relevance, k
                ),
            }

            # Candidate recall is measured BEFORE reranking.
            candidate_ids = _retrieved_external_ids(
                rerank_candidates,
                external_id_by_uuid,
            )

            per_case[case.case_id]["candidate_retrieved_ids"][
                "hybrid_reranked"
            ] = candidate_ids

            per_case[case.case_id]["candidate_recall"][
                "hybrid_reranked"
            ] = {
                f"recall@{depth}": recall_at_k(
                    candidate_ids, relevant, depth
                )
                for depth in (5, 10, 20)
            }

            # -----------------------------------------------------
            # Experimental strategy: Hybrid + RRF/TinyBERT fusion.
            # -----------------------------------------------------

            fusion_started = time.perf_counter()

            fused_results, fusion_diagnostics = (
                _fuse_hybrid_and_reranker(
                    rerank_candidates,
                    reranked_results,
                )
            )

            fused_top_k = fused_results[:k]

            fusion_ms = (
                time.perf_counter() - fusion_started
            ) * 1000

            fusion_samples.append(fusion_ms)

            fused_ids = _retrieved_external_ids(
                fused_top_k,
                external_id_by_uuid,
            )

            # Total latency includes candidate retrieval, reranking,
            # and the additional fusion operation.
            fused_total_ms = (
                time.perf_counter() - reranked_started
            ) * 1000

            retrieval_samples["hybrid_fused"].append(
                fused_total_ms
            )

            rankings["hybrid_fused"].append(fused_ids)

            per_case[case.case_id]["retrieved_ids"][
                "hybrid_fused"
            ] = fused_ids

            per_case[case.case_id]["latency_ms"][
                "hybrid_fused"
            ] = fused_total_ms

            per_case[case.case_id]["metrics"][
                "hybrid_fused"
            ] = {
                f"precision@{k}": precision_at_k(
                    fused_ids, relevant, k
                ),
                f"recall@{k}": recall_at_k(
                    fused_ids, relevant, k
                ),
                "mrr": mean_reciprocal_rank(
                    [fused_ids], [relevant]
                ),
                f"ndcg@{k}": ndcg_at_k(
                    fused_ids, relevance, k
                ),
            }

            # Evaluate weighted hybrid/reranker fusion variants.
            for strategy, hybrid_weight in (
                ("hybrid_weighted_025", 0.25),
                ("hybrid_weighted_050", 0.50),
                ("hybrid_weighted_075", 0.75),
            ):
                weighted_started = time.perf_counter()
                weighted_results, _ = _fuse_hybrid_and_reranker(
                    rerank_candidates,
                    reranked_results,
                    hybrid_weight=hybrid_weight,
                )
                weighted_ids = _retrieved_external_ids(
                    weighted_results[:k],
                    external_id_by_uuid,
                )
                weighted_fusion_ms = (
                    time.perf_counter() - weighted_started
                ) * 1000
                weighted_total_ms = reranked_total_ms + weighted_fusion_ms

                rankings[strategy].append(weighted_ids)
                retrieval_samples[strategy].append(weighted_total_ms)

                per_case[case.case_id]["retrieved_ids"][strategy] = weighted_ids
                per_case[case.case_id]["latency_ms"][strategy] = weighted_total_ms
                per_case[case.case_id]["metrics"][strategy] = {
                    f"precision@{k}": precision_at_k(weighted_ids, relevant, k),
                    f"recall@{k}": recall_at_k(weighted_ids, relevant, k),
                    "mrr": mean_reciprocal_rank([weighted_ids], [relevant]),
                    f"ndcg@{k}": ndcg_at_k(weighted_ids, relevance, k),
                }
                per_case[case.case_id]["candidate_retrieved_ids"][strategy] = candidate_ids
                per_case[case.case_id]["candidate_recall"][strategy] = (
                    per_case[case.case_id]["candidate_recall"]["hybrid_reranked"]
                )

            per_case[case.case_id]["candidate_retrieved_ids"][
                "hybrid_fused"
            ] = candidate_ids

            per_case[case.case_id]["candidate_recall"][
                "hybrid_fused"
            ] = per_case[case.case_id]["candidate_recall"][
                "hybrid_reranked"
            ]

            per_case[case.case_id]["fusion_diagnostics"] = (
                fusion_diagnostics
            )

        # Aggregate metrics across all benchmark cases.
        aggregate = {
            strategy: _calculate_metrics(
                rankings[strategy],
                relevant_sets,
                relevance_maps,
                k,
            )
            for strategy in STRATEGIES
        }

        # Run threshold experiments on the same committed evidence corpus.
        # Lexical retrieval is threshold-independent.
        # Reranking and fusion are deliberately excluded.
        threshold_sensitivity, threshold_latency = (
            _run_threshold_sensitivity(
                retriever=retriever,
                cases=cases,
                evidence_ids=evaluation_evidence_ids,
                external_id_by_uuid=external_id_by_uuid,
                relevant_sets=relevant_sets,
                relevance_maps=relevance_maps,
                k=k,
            )
        )

        latency_report = {
            "document_embedding": _latency_summary(
                document_embedding_times
            ),
            "query_embedding": _latency_summary(
                query_embedding_times
            ),
            "vector_retrieval": _latency_summary(
                retrieval_samples["vector"]
            ),
            "lexical_retrieval": _latency_summary(
                retrieval_samples["lexical"]
            ),
            "hybrid_retrieval": _latency_summary(
                retrieval_samples["hybrid"]
            ),
            "hybrid_reranked": _latency_summary(
                retrieval_samples["hybrid_reranked"]
            ),
            "hybrid_fused": _latency_summary(
                retrieval_samples["hybrid_fused"]
            ),
            "hybrid_weighted_025": _latency_summary(
                retrieval_samples["hybrid_weighted_025"]
            ),
            "hybrid_weighted_050": _latency_summary(
                retrieval_samples["hybrid_weighted_050"]
            ),
            "hybrid_weighted_075": _latency_summary(
                retrieval_samples["hybrid_weighted_075"]
            ),
            "reranking_only": _latency_summary(
                reranking_samples
            ),
            "fusion_only": _latency_summary(
                fusion_samples
            ),
            "reranker_warmup": _latency_summary(
                [reranker_warmup_ms]
            ),
        }

        # Snapshot cache statistics after all benchmark operations.
        embedding_cache_stats = (
            retriever.embedding_service.cache.stats
        )

        print("\nEMBEDDING CACHE STATISTICS")
        print("-" * 40)

        for name, value in embedding_cache_stats.items():
            print(f"{name:<16}: {value}")

        _print_report(aggregate, per_case, latency_report, k)

        _print_threshold_report(
            threshold_sensitivity,
            threshold_latency,
            k,
        )

        report = {
            "evaluation_type": "shared_corpus",
            "case_count": len(cases),
            "corpus_size": len(evaluation_evidence_ids),
            "k": k,
            "rrf_k": RRF_K,
            "rerank_candidate_limit": RERANK_CANDIDATE_LIMIT,
            "aggregate": aggregate,
            "threshold_sensitivity": threshold_sensitivity,
            "threshold_latency": threshold_latency,
            "latency": latency_report,
            "embedding_cache": embedding_cache_stats,
            "per_case": per_case,
        }

        print("\nJSON REPORT")
        print(json.dumps(report, indent=2))

        return report

    finally:
        session.rollback()

        try:
            temporary_investigation = (
                session.query(Investigation)
                .filter(Investigation.id == investigation_id)
                .one_or_none()
            )

            if temporary_investigation is not None:
                session.delete(temporary_investigation)
                session.commit()

        except Exception:
            session.rollback()
            raise

        finally:
            session.close()


if __name__ == "__main__":
    run_benchmark()