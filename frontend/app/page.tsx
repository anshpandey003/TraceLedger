import AppShell from "@/components/layout/AppShell";
import MetricCard from "@/components/dashboard/MetricCard";
import InvestigationList from "@/components/dashboard/InvestigationList";
import EvidenceQuality from "@/components/dashboard/EvidenceQuality";
import EvidenceTimeline from "@/components/dashboard/EvidenceTimeline";
import AssistantCard from "@/components/dashboard/AssistantCard";

export default function DashboardPage() {
  return (
    <AppShell>
      <section className="metrics-grid">
        <MetricCard
          label="Total investigations"
          value={127}
          meta="Across this workspace"
        />

        <MetricCard
          label="Completed"
          value={89}
          meta="70% of investigations"
        />

        <MetricCard
          label="Contradicted"
          value={21}
          meta="Evidence conflict detected"
        />

        <MetricCard
          label="Inconclusive"
          value={11}
          meta="More evidence may be needed"
        />
      </section>

      <div className="dashboard-grid">
        <InvestigationList />

        <div className="right-column">
          <EvidenceQuality />

          <EvidenceTimeline />

          <AssistantCard />
        </div>
      </div>
    </AppShell>
  );
}