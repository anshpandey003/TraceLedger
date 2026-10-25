export type ClaimStatus =
  | "pending"
  | "investigating"
  | "completed"
  | "failed";

export interface Claim {
  id: string;
  investigation_id: string;
  text: string;
  scope: string;
  as_of: string;
  status: ClaimStatus;
  created_at: string;
}