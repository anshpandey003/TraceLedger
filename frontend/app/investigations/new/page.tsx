
"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";

import AppShell from "@/components/layout/AppShell";
import { apiPost } from "@/lib/api/client";
import type { Investigation } from "@/lib/types/investigation";

export default function NewInvestigationPage() {
  const router = useRouter();

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const cleanTitle = title.trim();

    if (!cleanTitle) {
      setError("An investigation title is required.");
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const investigation = await apiPost<
        Investigation,
        { title: string; description: string | null }
      >("/investigations/", {
        title: cleanTitle,
        description: description.trim() || null,
      });

      router.push(`/investigations/${investigation.id}`);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Something went wrong while creating the investigation.",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <AppShell>
      <div className="new-investigation-page">
        <header className="new-investigation-header">
          <button
            type="button"
            className="new-investigation-back"
            onClick={() => router.push("/")}
          >
            <span aria-hidden="true">â†</span>
            <span>Back to workspace</span>
          </button>

          <div className="new-investigation-heading">
            <div className="new-investigation-icon" aria-hidden="true">
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.7"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M12 3 19 6v5c0 4.5-2.8 7.7-7 10-4.2-2.3-7-5.5-7-10V6l7-3Z" />
                <path d="m9 12 2 2 4-4" />
              </svg>
            </div>

            <div>
              <p className="new-investigation-eyebrow">
                TRACELEDGER / WORKSPACE
              </p>
              <h1>Start an investigation</h1>
              <p className="new-investigation-subtitle">
                Give your investigation a clear focus. You can add the
                claim and supporting evidence next.
              </p>
            </div>
          </div>
        </header>

        <div className="new-investigation-layout">
          <section className="new-investigation-card">
            <div className="new-investigation-card-header">
              <div>
                <p className="new-investigation-step">STEP 01 OF 03</p>
                <h2>Investigation details</h2>
                <p>Start with the essentials. You can refine these later.</p>
              </div>

              <span className="new-investigation-step-count">01</span>
            </div>

            <div className="new-investigation-progress" aria-label="Step 1 of 3">
              <span className="active" />
              <span />
              <span />
            </div>

            <form
              onSubmit={handleSubmit}
              className="new-investigation-form"
            >
              <div className="new-investigation-field">
                <label htmlFor="investigation-title">
                  Investigation name <span>*</span>
                </label>

                <input
                  id="investigation-title"
                  type="text"
                  value={title}
                  onChange={(event) => setTitle(event.target.value)}
                  placeholder="e.g. Verify a reported product recall"
                  maxLength={255}
                  required
                  autoFocus
                  disabled={loading}
                />

                <div className="new-investigation-field-footer">
                  <span>Choose a name that&apos;s easy to recognize.</span>
                  <span>{title.length}/255</span>
                </div>
              </div>

              <div className="new-investigation-field">
                <label htmlFor="investigation-description">
                  Context <span className="optional">(OPTIONAL)</span>
                </label>

                <textarea
                  id="investigation-description"
                  value={description}
                  onChange={(event) => setDescription(event.target.value)}
                  placeholder="What are you trying to establish? Add relevant context, scope, or questions..."
                  rows={6}
                  disabled={loading}
                />

                <div className="new-investigation-field-footer">
                  <span>Context helps keep the investigation organized.</span>
                </div>
              </div>

              {error && (
                <div className="new-investigation-error" role="alert">
                  <strong>Investigation not created</strong>
                  <p>{error}</p>
                </div>
              )}

              <div className="new-investigation-actions">
                <button
                  type="button"
                  className="new-investigation-cancel"
                  onClick={() => router.push("/")}
                  disabled={loading}
                >
                  Cancel
                </button>

                <button
                  type="submit"
                  className="new-investigation-submit"
                  disabled={loading || !title.trim()}
                >
                  {loading ? (
                    <>
                      <span className="new-investigation-spinner" />
                      Creating...
                    </>
                  ) : (
                    <>
                      Create investigation
                      <span aria-hidden="true">â†’</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          </section>

          <aside className="new-investigation-aside">
            <div className="new-investigation-aside-top">
              <span className="new-investigation-aside-mark">
                <svg
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.6"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  aria-hidden="true"
                >
                  <path d="M12 3 19 6v5c0 4.5-2.8 7.7-7 10-4.2-2.3-7-5.5-7-10V6l7-3Z" />
                  <path d="m9 12 2 2 4-4" />
                </svg>
              </span>
              <p>HOW IT WORKS</p>
            </div>

            <h2>From claim to evidence-backed conclusion.</h2>
            <p className="new-investigation-aside-description">
              TraceLedger helps organize evidence, evaluate conflicting
              claims, and explain the basis for an investigation&apos;s result.
            </p>

            <div className="new-investigation-steps">
              <div className="new-investigation-aside-step">
                <span className="new-investigation-aside-number active">
                  01
                </span>
                <div>
                  <h3>Create an investigation</h3>
                  <p>Define the scope and purpose.</p>
                </div>
              </div>

              <div className="new-investigation-aside-connector" />

              <div className="new-investigation-aside-step">
                <span className="new-investigation-aside-number">02</span>
                <div>
                  <h3>Add a claim and evidence</h3>
                  <p>Bring together sources and supporting facts.</p>
                </div>
              </div>

              <div className="new-investigation-aside-connector" />

              <div className="new-investigation-aside-step">
                <span className="new-investigation-aside-number">03</span>
                <div>
                  <h3>Run verification</h3>
                  <p>Review findings, conflicts, and citations.</p>
                </div>
              </div>
            </div>

            <div className="new-investigation-note">
              <span aria-hidden="true">i</span>
              <p>
                Creating an investigation doesn&apos;t verify a claim by itself.
                Verification happens after you add the relevant evidence
                and run the investigation.
              </p>
            </div>
          </aside>
        </div>
      </div>

      <style jsx>{`
        .new-investigation-page {
          --ni-accent: var(--accent, #6d7cff);
          --ni-text: var(--text-primary, #f1f3fa);
          --ni-muted: var(--text-secondary, #969db1);
          --ni-border: var(--border, rgba(145, 155, 180, 0.18));
          padding: 12px 0 36px;
          color: var(--ni-text);
        }

        .new-investigation-header {
          margin-bottom: 30px;
        }

        .new-investigation-back {
          display: inline-flex;
          align-items: center;
          gap: 9px;
          padding: 0;
          margin-bottom: 27px;
          border: 0;
          background: transparent;
          color: var(--ni-muted);
          font-size: 13px;
          cursor: pointer;
        }

        .new-investigation-back:hover {
          color: var(--ni-text);
        }

        .new-investigation-back span:first-child {
          font-size: 18px;
        }

        .new-investigation-heading {
          display: flex;
          align-items: flex-start;
          gap: 17px;
        }

        .new-investigation-icon,
        .new-investigation-aside-mark {
          display: grid;
          place-items: center;
          flex-shrink: 0;
          color: var(--ni-accent);
          background: color-mix(in srgb, var(--ni-accent) 12%, transparent);
          border: 1px solid
            color-mix(in srgb, var(--ni-accent) 24%, transparent);
          border-radius: 13px;
        }

        .new-investigation-icon {
          width: 48px;
          height: 48px;
        }

        .new-investigation-icon svg {
          width: 24px;
          height: 24px;
        }

        .new-investigation-eyebrow,
        .new-investigation-step,
        .new-investigation-aside-top > p {
          margin: 0;
          color: var(--ni-muted);
          font-size: 10px;
          font-weight: 700;
          letter-spacing: 1.5px;
        }

        .new-investigation-heading h1 {
          margin: 7px 0 9px;
          color: var(--ni-text);
          font-size: clamp(26px, 3vw, 34px);
          line-height: 1.2;
          font-weight: 700;
          letter-spacing: -1.1px;
        }

        .new-investigation-subtitle {
          max-width: 610px;
          margin: 0;
          color: var(--ni-muted);
          font-size: 14px;
          line-height: 1.75;
        }

        .new-investigation-layout {
          display: grid;
          grid-template-columns: minmax(0, 1.65fr) minmax(260px, 0.9fr);
          align-items: start;
          gap: 22px;
        }

        .new-investigation-card,
        .new-investigation-aside {
          min-width: 0;
          border: 1px solid var(--ni-border);
          border-radius: 17px;
          background: var(--surface, rgba(255, 255, 255, 0.025));
        }

        .new-investigation-card {
          overflow: hidden;
        }

        .new-investigation-card-header {
          display: flex;
          align-items: flex-start;
          justify-content: space-between;
          gap: 15px;
          padding: 27px 28px 22px;
        }

        .new-investigation-card-header h2 {
          margin: 9px 0 7px;
          font-size: 19px;
          font-weight: 650;
          letter-spacing: -0.35px;
        }

        .new-investigation-card-header > div > p:last-child {
          margin: 0;
          color: var(--ni-muted);
          font-size: 12px;
          line-height: 1.6;
        }

        .new-investigation-step-count {
          display: grid;
          place-items: center;
          width: 39px;
          height: 39px;
          flex-shrink: 0;
          border: 1px solid var(--ni-border);
          border-radius: 11px;
          color: var(--ni-muted);
          font-size: 13px;
          font-weight: 650;
        }

        .new-investigation-progress {
          display: grid;
          grid-template-columns: repeat(3, minmax(0, 1fr));
          gap: 5px;
          padding: 0 28px 25px;
        }

        .new-investigation-progress span {
          height: 3px;
          border-radius: 10px;
          background: var(--ni-border);
        }

        .new-investigation-progress span.active {
          background: var(--ni-accent);
        }

        .new-investigation-form {
          padding: 26px 28px 27px;
          border-top: 1px solid var(--ni-border);
        }

        .new-investigation-field {
          margin-bottom: 25px;
        }

        .new-investigation-field label {
          display: flex;
          align-items: center;
          gap: 5px;
          margin-bottom: 10px;
          color: var(--ni-text);
          font-size: 12px;
          font-weight: 650;
        }

        .new-investigation-field label > span:first-child {
          color: #ed818b;
        }

        .new-investigation-field label .optional {
          margin-left: auto;
          color: var(--ni-muted);
          font-size: 9px;
          font-weight: 600;
          letter-spacing: 0.8px;
        }

        .new-investigation-field input,
        .new-investigation-field textarea {
          display: block;
          width: 100%;
          box-sizing: border-box;
          border: 1px solid var(--ni-border);
          border-radius: 10px;
          outline: none;
          background: var(--input-background, rgba(0, 0, 0, 0.08));
          color: var(--ni-text);
          font: inherit;
          font-size: 13px;
          transition:
            border-color 160ms ease,
            box-shadow 160ms ease;
        }

        .new-investigation-field input {
          min-height: 47px;
          padding: 0 14px;
        }

        .new-investigation-field textarea {
          min-height: 140px;
          padding: 13px 14px;
          resize: vertical;
          line-height: 1.65;
        }

        .new-investigation-field input::placeholder,
        .new-investigation-field textarea::placeholder {
          color: var(--ni-muted);
          opacity: 0.75;
        }

        .new-investigation-field input:focus,
        .new-investigation-field textarea:focus {
          border-color: var(--ni-accent);
          box-shadow: 0 0 0 3px
            color-mix(in srgb, var(--ni-accent) 14%, transparent);
        }

        .new-investigation-field input:disabled,
        .new-investigation-field textarea:disabled {
          opacity: 0.65;
          cursor: not-allowed;
        }

        .new-investigation-field-footer {
          display: flex;
          justify-content: space-between;
          gap: 12px;
          margin-top: 8px;
          color: var(--ni-muted);
          font-size: 10px;
          line-height: 1.5;
        }

        .new-investigation-error {
          padding: 13px 15px;
          margin-bottom: 22px;
          border: 1px solid rgba(235, 103, 118, 0.3);
          border-radius: 10px;
          background: rgba(235, 103, 118, 0.07);
          color: #ef9aa4;
          font-size: 12px;
          overflow-wrap: anywhere;
        }

        .new-investigation-error p {
          margin: 6px 0 0;
          line-height: 1.6;
        }

        .new-investigation-actions {
          display: flex;
          align-items: center;
          justify-content: flex-end;
          gap: 10px;
          padding-top: 22px;
          border-top: 1px solid var(--ni-border);
        }

        .new-investigation-cancel,
        .new-investigation-submit {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          gap: 10px;
          min-height: 42px;
          padding: 0 16px;
          border-radius: 9px;
          font-size: 12px;
          font-weight: 650;
          cursor: pointer;
          transition:
            transform 160ms ease,
            background 160ms ease,
            border-color 160ms ease;
        }

        .new-investigation-cancel {
          border: 1px solid var(--ni-border);
          background: transparent;
          color: var(--ni-text);
        }

        .new-investigation-cancel:hover:not(:disabled) {
          background: rgba(255, 255, 255, 0.045);
        }

        .new-investigation-submit {
          border: 1px solid transparent;
          background: var(--ni-accent);
          color: #fff;
        }

        .new-investigation-submit:hover:not(:disabled) {
          transform: translateY(-1px);
          filter: brightness(1.08);
        }

        .new-investigation-submit:disabled,
        .new-investigation-cancel:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .new-investigation-spinner {
          width: 13px;
          height: 13px;
          border: 2px solid rgba(255, 255, 255, 0.4);
          border-top-color: #fff;
          border-radius: 50%;
          animation: ni-spin 0.7s linear infinite;
        }

        .new-investigation-aside {
          padding: 25px 23px 22px;
        }

        .new-investigation-aside-top {
          display: flex;
          align-items: center;
          gap: 10px;
          margin-bottom: 19px;
        }

        .new-investigation-aside-mark {
          width: 33px;
          height: 33px;
          border-radius: 9px;
        }

        .new-investigation-aside-mark svg {
          width: 18px;
          height: 18px;
        }

        .new-investigation-aside h2 {
          margin: 0 0 11px;
          font-size: 18px;
          line-height: 1.45;
          font-weight: 650;
          letter-spacing: -0.4px;
        }

        .new-investigation-aside-description {
          margin: 0;
          color: var(--ni-muted);
          font-size: 12px;
          line-height: 1.8;
        }

        .new-investigation-steps {
          margin-top: 26px;
        }

        .new-investigation-aside-step {
          display: flex;
          align-items: flex-start;
          gap: 12px;
        }

        .new-investigation-aside-number {
          display: grid;
          place-items: center;
          width: 32px;
          height: 32px;
          flex-shrink: 0;
          border: 1px solid var(--ni-border);
          border-radius: 9px;
          color: var(--ni-muted);
          font-size: 10px;
          font-weight: 700;
        }

        .new-investigation-aside-number.active {
          border-color: color-mix(in srgb, var(--ni-accent) 40%, transparent);
          background: color-mix(in srgb, var(--ni-accent) 12%, transparent);
          color: var(--ni-accent);
        }

        .new-investigation-aside-step h3 {
          margin: 2px 0 5px;
          font-size: 12px;
          font-weight: 650;
          line-height: 1.5;
        }

        .new-investigation-aside-step p {
          margin: 0;
          color: var(--ni-muted);
          font-size: 11px;
          line-height: 1.65;
        }

        .new-investigation-aside-connector {
          width: 1px;
          height: 22px;
          margin: 5px 0 5px 15px;
          background: var(--ni-border);
        }

        .new-investigation-note {
          display: flex;
          align-items: flex-start;
          gap: 10px;
          padding: 13px;
          margin-top: 26px;
          border: 1px solid var(--ni-border);
          border-radius: 10px;
          background: rgba(255, 255, 255, 0.02);
        }

        .new-investigation-note > span {
          display: grid;
          place-items: center;
          width: 17px;
          height: 17px;
          flex-shrink: 0;
          border: 1px solid var(--ni-muted);
          border-radius: 50%;
          color: var(--ni-muted);
          font-size: 10px;
          font-weight: 700;
        }

        .new-investigation-note p {
          margin: 0;
          color: var(--ni-muted);
          font-size: 10px;
          line-height: 1.8;
        }

        @keyframes ni-spin {
          to {
            transform: rotate(360deg);
          }
        }

        @media (max-width: 1050px) {
          .new-investigation-layout {
            grid-template-columns: minmax(0, 1fr);
          }

          .new-investigation-aside {
            display: none;
          }
        }

        @media (max-width: 600px) {
          .new-investigation-page {
            padding-top: 4px;
          }

          .new-investigation-heading {
            gap: 12px;
          }

          .new-investigation-icon {
            width: 40px;
            height: 40px;
          }

          .new-investigation-card-header,
          .new-investigation-form {
            padding-right: 18px;
            padding-left: 18px;
          }

          .new-investigation-progress {
            padding-right: 18px;
            padding-left: 18px;
          }

          .new-investigation-actions {
            flex-wrap: wrap;
          }

          .new-investigation-submit {
            flex: 1;
          }
        }

        @media (prefers-reduced-motion: reduce) {
          .new-investigation-page *,
          .new-investigation-page *::before,
          .new-investigation-page *::after {
            animation-duration: 0.01ms !important;
            transition-duration: 0.01ms !important;
          }
        }
      `}</style>
    </AppShell>
  );
}
