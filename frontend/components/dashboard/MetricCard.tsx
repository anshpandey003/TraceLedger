type MetricCardProps = {
  label: string;
  value: string | number;
  meta: string;
};

export default function MetricCard({
  label,
  value,
  meta,
}: MetricCardProps) {
  return (
    <div className="metric-card">
      <div className="metric-label">
        {label}
      </div>

      <div className="metric-value">
        {value}
      </div>

      <div className="metric-meta">
        {meta}
      </div>
    </div>
  );
}