"use client";

import { useTheme } from "@/components/theme/ThemeProvider";

export default function Topbar() {
  const { theme, toggleTheme } = useTheme();

  return (
    <header className="topbar">
      <div>
        <div className="eyebrow">Investigation workspace</div>

        <h1>Good afternoon.</h1>

        <p className="page-description">
          Review what TraceLedger has investigated and what still needs
          your attention.
        </p>
      </div>

      <div className="topbar-actions">
        <button
          type="button"
          className="secondary-button theme-toggle"
          onClick={toggleTheme}
          aria-label={`Switch to ${theme === "light" ? "dark" : "light"} mode`}
          title={`Switch to ${theme === "light" ? "dark" : "light"} mode`}
        >
          <span aria-hidden="true">
            {theme === "light" ? "\u263E" : "\u2600"}
          </span>
          <span>{theme === "light" ? "Dark mode" : "Light mode"}</span>
        </button>
      </div>
    </header>
  );
}
