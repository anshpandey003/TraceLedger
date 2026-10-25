"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import AppShell from "@/components/layout/AppShell";
import { apiGet } from "@/lib/api/client";
import type { Evidence } from "@/lib/types/evidence";

type EvidencePageProps = {
  params: Promise<{
    id: string;
    claimId: string;
    evidenceId: string;
  }>;
};

export default function EvidencePage({
  params,
}: EvidencePageProps) {
  const [evidence, setEvidence] = useState<Evidence | null>(null);
  const [investigationId, setInvestigationId] =
    useState<string | null>(null);
  const [claimId, setClaimId] = useState<string | null>(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadEvidence() {
      try {
        setLoading(true);
        setError(null);

        const {
          id,
          claimId: currentClaimId,
          evidenceId,
        } = await params;

        setInvestigationId(id);
        setClaimId(currentClaimId);

        const evidenceData = await apiGet<Evidence>(
          `/claims/${currentClaimId}/evidence/${evidenceId}`,
        );

        setEvidence(evidenceData);
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Failed to load evidence.",
        );
      } finally {
        setLoading(false);
      }
    }

    loadEvidence();
  }, [params]);

  if (loading) {
    return (
      <AppShell>
        <div className="empty-search">
          Loading evidence...
        </div>
      </AppShell>
    );
  }

  if (error || !evidence) {
    return (
      <AppShell>
        <Link
          href={
            investigationId
              ? `/investigations/${investigationId}`
              : "/"
          }
          className="text-button"
        >
          ← Back to investigation
        </Link>

        <div className="empty-search">
          Unable to load evidence.
          <span>{error ?? "Evidence not found."}</span>
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <div
        style={{
          display: "flex",
          alignItems: "flex-start",
          justifyContent: "space-between",
          gap: "24px",
          marginBottom: "28px",
        }}
      >
        <div>
          <p className="eyebrow">Evidence</p>

          <h1
            style={{
              margin: "4px 0 8px",
              fontFamily:
                'Georgia, "Times New Roman", serif',
              fontSize: "clamp(30px, 4vw, 42px)",
              lineHeight: "1.08",
              letterSpacing: "-0.035em",
              color: "var(--foreground)",
            }}
          >
            {evidence.title ?? "Untitled source"}
          </h1>

          <p className="page-description">
            Inspect the source used during the investigation.
          </p>
        </div>

        <div className="topbar-actions">
          <Link
            href={
              investigationId
                ? `/investigations/${investigationId}`
                : "/"
            }
            className="secondary-button"
          >
            ← Investigation
          </Link>
        </div>
      </div>

      <section className="panel">
        <div className="panel-header">
          <div>
            <p className="eyebrow">Source</p>
            <h2>Evidence details</h2>
          </div>

          {evidence.authority && (
            <span className="evidence-authority">
              {evidence.authority}
            </span>
          )}
        </div>

        <div className="evidence-detail-meta">
          {evidence.published_at && (
            <div>
              <span className="detail-label">
                Published
              </span>

              <p className="detail-value">
                {new Date(
                  evidence.published_at,
                ).toLocaleString("en-IN")}
              </p>
            </div>
          )}

          {evidence.observed_at && (
            <div>
              <span className="detail-label">
                Observed
              </span>

              <p className="detail-value">
                {new Date(
                  evidence.observed_at,
                ).toLocaleString("en-IN")}
              </p>
            </div>
          )}

          <div>
            <span className="detail-label">
              Retrieved
            </span>

            <p className="detail-value">
              {new Date(
                evidence.retrieved_at,
              ).toLocaleString("en-IN")}
            </p>
          </div>
        </div>
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <p className="eyebrow">Source content</p>
            <h2>Evidence</h2>
          </div>
        </div>

        <div className="evidence-detail-content">
          {evidence.content}
        </div>
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <p className="eyebrow">Identifiers</p>
            <h2>Traceability</h2>
          </div>
        </div>

        <div className="investigation-detail-grid">
          <div>
            <span className="detail-label">
              Evidence ID
            </span>

            <p className="detail-value">
              {evidence.id}
            </p>
          </div>

          <div>
            <span className="detail-label">
              Claim ID
            </span>

            <p className="detail-value">
              {claimId}
            </p>
          </div>

          {evidence.source_url && (
            <div>
              <span className="detail-label">
                Source URL
              </span>

              <p className="detail-value">
                <a
                  href={evidence.source_url}
                  target="_blank"
                  rel="noreferrer"
                  className="source-link"
                >
                  Open source ↗
                </a>
              </p>
            </div>
          )}
        </div>
      </section>
    </AppShell>
  );
}