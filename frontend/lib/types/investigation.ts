export type InvestigationStatus =
  | "pending"
  | "running"
  | "completed"
  | "failed";

export interface Investigation {
  id: string;
  title: string;
  description: string;
  status: InvestigationStatus;
  created_at: string;
  updated_at: string;
}