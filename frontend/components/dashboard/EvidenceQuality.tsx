import QualityBar from "../ui/QualityBar";

export default function EvidenceQuality() {
  return (
    <section className="panel">
      <div className="panel-header compact">
        <div>
          <h2>Evidence quality</h2>

          <p>
            Across recent investigations.
          </p>
        </div>

        <button className="text-button">
          Details
        </button>
      </div>

      <div className="quality-list">
        <QualityBar
          label="Authority"
          value={92}
        />

        <QualityBar
          label="Temporal validity"
          value={88}
        />

        <QualityBar
          label="Evidence coverage"
          value={84}
        />
      </div>
    </section>
  );
}