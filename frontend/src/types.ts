export interface SubScoreImperative {
  score: number | null;
  status: string;
  is_imperative: boolean;
  first_word: string;
  inflection: string;
  suggestion: string | null;
  evidence: string;
  ambiguous?: boolean;
}

export interface SubScoreCoverage {
  score: number | null;
  status: string;
  mentioned_symbols: string[];
  omitted_symbols: string[];
  total_symbols: number;
  evidence: string;
}

export interface SubScoreRisk {
  score: number | null;
  status: string;
  flags: string[];
  sensitive_files: string[];
  layers_triggered: string[];
  evidence: string;
}

export interface SubScoreTypeConsistency {
  score: number | null;
  status: string;
  predicted_message_type: string;
  diff_inferred_type: string;
  evidence: string;
}

export interface AuditScores {
  imperative_mood: SubScoreImperative;
  coverage: SubScoreCoverage;
  risk_flags: SubScoreRisk;
  type_consistency: SubScoreTypeConsistency;
}

export interface DiffSummary {
  files: string[];
  added_lines: number;
  removed_lines: number;
  symbols: string[];
  file_summaries?: Array<{
    file: string;
    added: number;
    removed: number;
    symbols?: string[];
  }>;
}

export interface AuditReport {
  commit_message: string;
  overall_score: number | null;
  overall_status: string;
  diff_inferred_type: string;
  message_intent: string;
  evidence?: string;
  scores: AuditScores;
  aggregation: {
    weights_used: Record<string, number>;
    missing_sub_scores: string[];
  };
  diff_summary: DiffSummary;
}

export interface CommitPreset {
  id: string;
  name: string;
  tag: string;
  badgeColor: string;
  description: string;
  message: string;
  diff: string;
}
