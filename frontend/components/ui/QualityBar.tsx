type QualityBarProps = {
  label: string;
  value: number;
};

export default function QualityBar({
  label,
  value,
}: QualityBarProps) {
  return (
    <div className="quality-item">
      <div className="quality-label-row">
        <span>{label}</span>
        <strong>{value}%</strong>
      </div>

      <div className="quality-track">
        <div
          className="quality-fill"
          style={{ width: `${value}%` }}
        />
      </div>
    </div>
  );
}