export default function AssistantCard() {
  return (
    <section className="assistant-card">
      <div className="assistant-header">
        <div>
          <div className="assistant-kicker">
            TRACELEDGER ASSISTANT
          </div>

          <h2>
            Investigate through conversation.
          </h2>
        </div>

        <span className="assistant-arrow">
          ↗
        </span>
      </div>

      <p>
        Ask TraceLedger to investigate a claim,
        explain a verdict, inspect evidence, or
        determine what was true at a particular
        point in time.
      </p>

      <button className="assistant-example">
        <span>
          “Was the refund limit ₹25,000 as of
          January 2026?”
        </span>

        <span className="assistant-example-arrow">
          →
        </span>
      </button>
    </section>
  );
}