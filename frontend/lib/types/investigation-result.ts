export type Verdict =
  | "supported"
  | "contradicted"
  | "inconclusive";

export interface InvestigationResult {
  id: string;
  claim_id: string;
  verdict: Verdict;
  explanation: string;
  confidence: number;
  created_at: string;
}