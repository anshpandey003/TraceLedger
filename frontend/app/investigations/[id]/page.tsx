
"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { apiGet } from "@/lib/api/client";
import type { Claim } from "@/lib/types/claim";
import type { Evidence } from "@/lib/types/evidence";
import type { Investigation } from "@/lib/types/investigation";
import type { InvestigationAnalysis } from "@/lib/types/investigation-analysis";
import type { InvestigationResult } from "@/lib/types/investigation-result";
import type { ResultCitation } from "@/lib/types/result-citation";

type InvestigationPageProps = {
  params: Promise<{
    id: string;
  }>;
};

type ClaimData = {
  claimId: string;
  evidence: Evidence[];
  result: InvestigationResult | null;
  citations: ResultCitation[];
  analysis: InvestigationAnalysis | null;
};

export default function InvestigationPage({
  params,
}: InvestigationPageProps) {
  const [investigation, setInvestigation] =
    useState<Investigation | null>(null);

  const [claims, setClaims] = useState<Claim[]>([]);

  const [claimDataById, setClaimDataById] = useState<
    Record<string, ClaimData>
  >({});

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadInvestigation() {
      try {
        setLoading(true);
        setError(null);

        const { id } = await params;

        const [investigationData, claimsData] = await Promise.all([
          apiGet<Investigation>(`/investigations/${id}`),
          apiGet<Claim[]>(`/investigations/${id}/claims`),
        ]);

        setInvestigation(investigationData);
        setClaims(claimsData);

        const claimData = await Promise.all(
          claimsData.map(async (claim) => {
            const [evidence, result] = await Promise.all([
              apiGet<Evidence[]>(`/claims/${claim.id}/evidence`),
              apiGet<InvestigationResult>(
                `/claims/${claim.id}/result`,
              ).catch(() => null),
            ]);

            let citations: ResultCitation[] = [];
            let analysis: InvestigationAnalysis | null = null;

            if (result) {
              const [citationsData, analysisData] = await Promise.all([
                apiGet<ResultCitation[]>(
                  `/claims/${claim.id}/result/${result.id}/citations`,
                ).catch(() => []),
                apiGet<InvestigationAnalysis>(
                  `/claims/${claim.id}/result/${result.id}/analysis/`,
                ).catch(() => null),
              ]);

              citations = citationsData;
              analysis = analysisData;
            }

            return {
              claimId: claim.id,
              evidence,
              result,
              citations,
              analysis,
            };
          }),
        );

        setClaimDataById(
          Object.fromEntries(
            claimData.map((item) => [item.claimId, item]),
          ),
        );
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Failed to load investigation.",
        );
      } finally {
        setLoading(false);
      }
    }

    loadInvestigation();
  }, [params]);

  if (loading) {
    return (
      <main className="main-content">
        <div className="empty-search">
          Loading investigation...
        </div>
      </main>
    );
  }

  if (error || !investigation) {
    return (
      <main className="main-content">
        <Link href="/" className="text-button">
          &larr; Back to dashboard
        </Link>

        <div className="empty-search">
          Unable to load investigation.
          <span>{error ?? "Investigation not found."}</span>
        </div>
      </main>
    );
  }

  return (
    <main className="main-content">
      <div className="topbar">
        <div>
          <p className="eyebrow">Investigation</p>

          <h1>{investigation.title}</h1>

          <p className="page-description">
            {investigation.description}
          </p>
        </div>

        <div className="topbar-actions">
          <Link href="/" className="secondary-button">
            &larr; Dashboard
          </Link>
        </div>
      </div>

      <section className="panel">
        <div className="panel-header">
          <div>
            <p className="eyebrow">Investigation details</p>
            <h2>Overview</h2>
          </div>

          <span
            className={`investigation-status-badge ${investigation.status}`}
          >
            {investigation.status}
          </span>
        </div>

        <div className="investigation-detail-grid">
          <div>
            <span className="detail-label">Investigation ID</span>
            <p className="detail-value">{investigation.id}</p>
          </div>

          <div>
            <span className="detail-label">Created</span>
            <p className="detail-value">
              {new Date(investigation.created_at).toLocaleString(
                "en-IN",
              )}
            </p>
          </div>

          <div>
            <span className="detail-label">Last updated</span>
            <p className="detail-value">
              {new Date(investigation.updated_at).toLocaleString(
                "en-IN",
              )}
            </p>
          </div>

          <div>
            <span className="detail-label">Status</span>
            <p className="detail-value">{investigation.status}</p>
          </div>
        </div>
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <p className="eyebrow">Claims</p>
            <h2>Claims under investigation</h2>
            <p>
              Claims being evaluated against available evidence.
            </p>
          </div>

          <span className="text-button">
            {claims.length}{" "}
            {claims.length === 1 ? "claim" : "claims"}
          </span>
        </div>

        {claims.length === 0 ? (
          <div className="empty-search">
            No claims found for this investigation.
          </div>
        ) : (
          <div className="claims-list">
            {claims.map((claim) => {
              const claimData = claimDataById[claim.id];

              const evidence = claimData?.evidence ?? [];
              const result = claimData?.result ?? null;
              const citations = claimData?.citations ?? [];
              const analysis = claimData?.analysis ?? null;
              const contradictions = analysis?.contradictions ?? [];

              const citedEvidenceIds = new Set(
                citations.map((citation) => citation.evidence_id),
              );

              return (
                <article className="claim-card" key={claim.id}>
                  <div className="claim-card-header">
                    <div>
                      <span className="detail-label">Claim</span>
                      <h3>{claim.text}</h3>
                    </div>

                    <span
                      className={`investigation-status-badge ${claim.status}`}
                    >
                      {claim.status}
                    </span>
                  </div>

                  <div className="claim-card-details">
                    <div>
                      <span className="detail-label">Scope</span>
                      <p className="detail-value">{claim.scope}</p>
                    </div>

                    <div>
                      <span className="detail-label">As of</span>
                      <p className="detail-value">
                        {new Date(claim.as_of).toLocaleDateString(
                          "en-IN",
                          {
                            day: "2-digit",
                            month: "short",
                            year: "numeric",
                          },
                        )}
                      </p>
                    </div>

                    <div>
                      <span className="detail-label">Evidence</span>
                      <p className="detail-value">
                        {evidence.length}{" "}
                        {evidence.length === 1 ? "source" : "sources"}
                      </p>
                    </div>

                    <div>
                      <span className="detail-label">Citations</span>
                      <p className="detail-value">
                        {citations.length}
                      </p>
                    </div>
                  </div>

                  {result && (
                    <div
                      className={`claim-result ${result.verdict}`}
                    >
                      <div className="claim-result-header">
                        <div>
                          <span className="detail-label">
                            Investigation result
                          </span>

                          <div className="claim-result-verdict">
                            {result.verdict}
                          </div>
                        </div>

                        <div className="claim-result-confidence">
                          <span className="detail-label">
                            Confidence
                          </span>

                          <strong>
                            {Math.round(result.confidence * 100)}%
                          </strong>
                        </div>
                      </div>

                      <p className="claim-result-explanation">
                        {result.explanation}
                      </p>

                      <div className="claim-result-meta">
                        <div>
                          <span className="detail-label">Evidence</span>
                          <p className="detail-value">
                            {evidence.length}{" "}
                            {evidence.length === 1
                              ? "source"
                              : "sources"}
                          </p>
                        </div>

                        <div>
                          <span className="detail-label">Cited</span>
                          <p className="detail-value">
                            {citations.length}{" "}
                            {citations.length === 1
                              ? "source"
                              : "sources"}
                          </p>
                        </div>

                        <div>
                          <span className="detail-label">As of</span>
                          <p className="detail-value">
                            {new Date(
                              claim.as_of,
                            ).toLocaleDateString("en-IN", {
                              day: "2-digit",
                              month: "short",
                              year: "numeric",
                            })}
                          </p>
                        </div>
                      </div>
                    </div>
                  )}

                  {result && (
                    <section className="claim-evidence">
                      <div className="claim-evidence-header">
                        <div>
                          <span className="detail-label">
                            Evidence analysis
                          </span>
                          <h4>Detected contradictions</h4>
                        </div>

                        <span className="text-button">
                          {contradictions.length}
                        </span>
                      </div>

                      {contradictions.length === 0 ? (
                        <div className="empty-search">
                          {analysis
                            ? "No contradictions were recorded for this result."
                            : "Contradiction analysis is currently unavailable."}
                        </div>
                      ) : (
                        <div className="evidence-list">
                          {contradictions.map((contradiction) => (
                            <article
                              className="evidence-card"
                              key={contradiction.id}
                            >
                              <div className="evidence-card-header">
                                <div>
                                  <span className="detail-label">
                                    Conflict type
                                  </span>

                                  <h5>
                                    {contradiction.conflict_type.replaceAll(
                                      "_",
                                      " ",
                                    )}
                                  </h5>
                                </div>
                              </div>

                              <p className="claim-result-explanation">
                                {contradiction.explanation}
                              </p>

                              <div className="evidence-meta">
                                <div>
                                  <span className="detail-label">
                                    Evidence A
                                  </span>

                                  <Link
                                    className="detail-value"
                                    href={`/investigations/${investigation.id}/claims/${claim.id}/evidence/${contradiction.evidence_a_id}`}
                                  >
                                    View source A &rarr;
                                  </Link>
                                </div>

                                <div>
                                  <span className="detail-label">
                                    Evidence B
                                  </span>

                                  <Link
                                    className="detail-value"
                                    href={`/investigations/${investigation.id}/claims/${claim.id}/evidence/${contradiction.evidence_b_id}`}
                                  >
                                    View source B &rarr;
                                  </Link>
                                </div>
                              </div>
                            </article>
                          ))}
                        </div>
                      )}
                    </section>
                  )}

                  <div className="claim-evidence">
                    <div className="claim-evidence-header">
                      <div>
                        <span className="detail-label">Evidence</span>
                        <h4>Supporting sources</h4>
                      </div>

                      <span className="text-button">
                        {evidence.length}
                      </span>
                    </div>

                    {evidence.length === 0 ? (
                      <div className="empty-search">
                        No evidence retrieved for this claim.
                      </div>
                    ) : (
                      <div className="evidence-list">
                        {evidence.map((item) => {
                          const isCited = citedEvidenceIds.has(item.id);

                          return (
                            <Link
                              key={item.id}
                              href={`/investigations/${investigation.id}/claims/${claim.id}/evidence/${item.id}`}
                              className="evidence-card evidence-card-link"
                            >
                              <div className="evidence-card-header">
                                <div>
                                  <span className="detail-label">
                                    Source
                                  </span>

                                  <h5>
                                    {item.title ?? "Untitled source"}
                                  </h5>
                                </div>

                                <div className="evidence-card-badges">
                                  {isCited && (
                                    <span className="citation-badge">
                                      &#10003; Cited
                                    </span>
                                  )}

                                  {item.authority && (
                                    <span className="evidence-authority">
                                      {item.authority}
                                    </span>
                                  )}
                                </div>
                              </div>

                              <p className="evidence-content">
                                {item.content}
                              </p>

                              <div className="evidence-meta">
                                {item.published_at && (
                                  <div>
                                    <span className="detail-label">
                                      Published
                                    </span>

                                    <p className="detail-value">
                                      {new Date(
                                        item.published_at,
                                      ).toLocaleDateString("en-IN", {
                                        day: "2-digit",
                                        month: "short",
                                        year: "numeric",
                                      })}
                                    </p>
                                  </div>
                                )}

                                {item.observed_at && (
                                  <div>
                                    <span className="detail-label">
                                      Observed
                                    </span>

                                    <p className="detail-value">
                                      {new Date(
                                        item.observed_at,
                                      ).toLocaleDateString("en-IN", {
                                        day: "2-digit",
                                        month: "short",
                                        year: "numeric",
                                      })}
                                    </p>
                                  </div>
                                )}

                                <div>
                                  <span className="detail-label">
                                    Retrieved
                                  </span>

                                  <p className="detail-value">
                                    {new Date(
                                      item.retrieved_at,
                                    ).toLocaleDateString("en-IN", {
                                      day: "2-digit",
                                      month: "short",
                                      year: "numeric",
                                    })}
                                  </p>
                                </div>
                              </div>

                              <div className="evidence-card-open">
                                View evidence &rarr;
                              </div>
                            </Link>
                          );
                        })}
                      </div>
                    )}
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </section>
    </main>
  );
}
