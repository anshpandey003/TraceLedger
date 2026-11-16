
"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { apiGet } from "@/lib/api/client";
import type { Investigation } from "@/lib/types/investigation";

export default function InvestigationList() {
  const router = useRouter();

  const [investigations, setInvestigations] = useState<Investigation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadInvestigations() {
      try {
        setLoading(true);
        setError(null);

        const data = await apiGet<Investigation[]>("/investigations");
        setInvestigations(data);
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Failed to load investigations.",
        );
      } finally {
        setLoading(false);
      }
    }

    loadInvestigations();
  }, []);

  if (loading) {
    return (
      <section className="panel investigations-panel">
        <div className="panel-header">
          <div>
            <p className="eyebrow">Investigations</p>
            <h2>Recent investigations</h2>
          </div>

          <button
            type="button"
            className="primary-button"
            onClick={() => router.push("/investigations/new")}
          >
            + New Investigation
          </button>
        </div>

        <div className="empty-search">Loading investigations...</div>
      </section>
    );
  }

  if (error) {
    return (
      <section className="panel investigations-panel">
        <div className="panel-header">
          <div>
            <p className="eyebrow">Investigations</p>
            <h2>Recent investigations</h2>
          </div>

          <button
            type="button"
            className="primary-button"
            onClick={() => router.push("/investigations/new")}
          >
            + New Investigation
          </button>
        </div>

        <div className="empty-search">
          Unable to load investigations.
          <span>{error}</span>
        </div>
      </section>
    );
  }

  return (
    <section className="panel investigations-panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Investigations</p>
          <h2>Recent investigations</h2>
          <p>Your latest evidence verification investigations.</p>
        </div>

        <div className="topbar-actions">
          <span className="text-button">
            {investigations.length} total
          </span>

          <button
            type="button"
            className="primary-button"
            onClick={() => router.push("/investigations/new")}
          >
            + New Investigation
          </button>
        </div>
      </div>

      {investigations.length === 0 ? (
        <div className="empty-search">
          No investigations yet. Create your first investigation to get
          started.
        </div>
      ) : (
        <>
          <div className="investigation-header">
            <span>Investigation</span>
            <span>Status</span>
            <span>Updated</span>
            <span>ID</span>
          </div>

          {investigations.map((investigation) => (
            <Link
              key={investigation.id}
              href={`/investigations/${investigation.id}`}
              className="investigation-row"
            >
              <div className="claim-cell">
                <div className="claim-title">{investigation.title}</div>

                <div className="claim-meta">
                  {investigation.description}
                </div>
              </div>

              <div>
                <span
                  className={`investigation-status-badge ${investigation.status}`}
                >
                  {investigation.status}
                </span>
              </div>

              <div className="confidence">
                {new Date(investigation.updated_at).toLocaleDateString(
                  "en-IN",
                  {
                    day: "2-digit",
                    month: "short",
                  },
                )}
              </div>

              <div className="evidence-count">
                {investigation.id.slice(0, 8)}…
              </div>
            </Link>
          ))}
        </>
      )}
    </section>
  );
}
