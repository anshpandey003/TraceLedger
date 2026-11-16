
"use client";

import { FormEvent, useState } from "react";
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

    if (!title.trim()) {
      setError("Please enter an investigation title.");
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const investigation = await apiPost<
        Investigation,
        { title: string; description: string | null }
      >("/investigations/", {
        title: title.trim(),
        description: description.trim() || null,
      });

      router.push(`/investigations/${investigation.id}`);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to create investigation.",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <AppShell>
      <div className="topbar">
        <div>
          <p className="eyebrow">Workspace</p>
          <h1>New investigation</h1>
          <p className="page-description">
            Set up an investigation before adding claims and evidence.
          </p>
        </div>
      </div>

      <section className="panel">
        <div className="panel-header">
          <div>
            <p className="eyebrow">Step 1</p>
            <h2>Investigation details</h2>
            <p>
              Give your investigation a clear title and optional context.
            </p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="investigation-form">
          <div className="form-field">
            <label htmlFor="title">Investigation title</label>
            <input
              id="title"
              name="title"
              type="text"
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              placeholder="e.g. Verify the reported product recall"
              maxLength={255}
              required
              autoFocus
            />
          </div>

          <div className="form-field">
            <label htmlFor="description">Description (optional)</label>
            <textarea
              id="description"
              name="description"
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              placeholder="Add context, the question being investigated, or the scope."
              rows={5}
            />
          </div>

          {error && (
            <div className="empty-search" role="alert">
              {error}
            </div>
          )}

          <div className="topbar-actions">
            <button
              type="button"
              className="secondary-button"
              onClick={() => router.push("/")}
              disabled={loading}
            >
              Cancel
            </button>

            <button
              type="submit"
              className="primary-button"
              disabled={loading || !title.trim()}
            >
              {loading ? "Creating..." : "Create investigation"}
            </button>
          </div>
        </form>
      </section>
    </AppShell>
  );
}
