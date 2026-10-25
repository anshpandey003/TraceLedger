import TimelineEvent from "../ui/TimelineEvent";

export default function EvidenceTimeline() {
  return (
    <section className="panel">
      <div className="panel-header compact">
        <div>
          <h2>Recent evidence</h2>

          <p>
            Latest evidence activity.
          </p>
        </div>

        <button className="text-button">
          Timeline
        </button>
      </div>

      <div className="timeline">
        <TimelineEvent
          date="25 SEP 2026"
          title="Refund documentation reviewed"
          description="Official source · maximum ₹25,000"
        />

        <TimelineEvent
          date="24 SEP 2026"
          title="Payment service evidence added"
          description="Production configuration snapshot"
        />

        <TimelineEvent
          date="21 SEP 2026"
          title="New investigation completed"
          description="5 evidence sources evaluated"
        />
      </div>
    </section>
  );
}