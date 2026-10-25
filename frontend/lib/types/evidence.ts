export interface Evidence {
  id: string;
  claim_id: string;
  title: string | null;
  content: string;
  source_url: string | null;
  published_at: string | null;
  observed_at: string | null;
  retrieved_at: string;
  authority: string | null;
  created_at: string;
}