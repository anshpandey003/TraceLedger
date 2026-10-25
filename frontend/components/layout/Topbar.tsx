export default function Topbar() {
  return (
    <header className="topbar">
      <div>
        <div className="eyebrow">
          Investigation workspace
        </div>

        <h1>
          Good afternoon.
        </h1>

        <p className="page-description">
          Review what TraceLedger has investigated
          and what still needs your attention.
        </p>
      </div>

      <div className="topbar-actions">
        <button className="secondary-button">
          <span>⌘</span>
          <span>K</span>
          <span className="search-label">
            Search
          </span>
        </button>

        <button className="primary-button">
          <span>+</span>
          <span>New Investigation</span>
        </button>
      </div>
    </header>
  );
}