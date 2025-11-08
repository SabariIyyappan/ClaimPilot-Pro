export interface Entity {
  text: string;
  label: string;
  start: number;
  end: number;
}

export interface CodeSuggestion {
  code: string;
  system: "ICD-10" | "CPT" | string;
  description: string;
  score: number;
  reason: string;
}

export interface UploadResponse {
  text: string;
  entities: Entity[];
}

export interface SuggestRequest {
  text: string;
  top_k?: number;
}

export interface SuggestResponse {
  entities: Entity[];
  suggestions: CodeSuggestion[];
}

export interface GenerateClaimRequest {
  approved: CodeSuggestion[];
  amount?: number;
  signed_by?: string;
}

export interface ClaimMetadata {
  pdf_url?: string;
  tx_hash?: string;
  explorer?: string;
}

export interface GenerateClaimResponse {
  claim_id: string;
  approved: CodeSuggestion[];
  metadata: ClaimMetadata;
}

export interface ClaimRecord {
  id: string;
  date: string;
  codes_count: number;
  amount?: number;
  tx_hash?: string;
}
