export type Verdict =
  | "supported"
  | "contradicted"
  | "inconclusive";

const labels: Record<Verdict, string> = {
  supported: "SUPPORTED",
  contradicted: "CONTRADICTED",
  inconclusive: "INCONCLUSIVE",
};

type VerdictBadgeProps = {
  verdict: Verdict;
};

export default function VerdictBadge({
  verdict,
}: VerdictBadgeProps) {
  return (
    <span className={`verdict-badge ${verdict}`}>
      {labels[verdict]}
    </span>
  );
}