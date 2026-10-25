
export interface ContradictionValue {
  assertion_type: string;
  raw_text: string;
  value: number;
  unit: string | null;
}

export interface ContradictionAnalysis {
  id: string;
  result_id: string;
  evidence_a_id: string;
  evidence_b_id: string;
  conflict_type: string;
  values_a: ContradictionValue[];
  values_b: ContradictionValue[];
  created_at: string;
  explanation: string;
}

export interface EvidenceAnalysis {
  id: string;
  result_id: string;
  evidence_id: string;
  authority_score: number;
  freshness_score: number;
  temporal_valid: boolean;
  completeness_score: number;
  created_at: string;
}

export interface InvestigationAnalysis {
  evidence_analysis: EvidenceAnalysis[];
  contradictions: ContradictionAnalysis[];
}
