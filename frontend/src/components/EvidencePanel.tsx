import {
  GitPullRequest,
  CheckCircle2,
  AlertTriangle,
  Check,
  GitCommit,
  SlidersHorizontal,
} from 'lucide-react';
import type { AuditReport } from '../types';

interface EvidencePanelProps {
  report: AuditReport;
  onApplyImperativeSuggestion: (suggested: string) => void;
}

export const EvidencePanel = ({ report, onApplyImperativeSuggestion }: EvidencePanelProps) => {
  const { scores, aggregation, commit_message } = report;
  const imp = scores.imperative_mood;
  const typeMatch = scores.type_consistency;

  return (
    <div className="bg-[#161b22] border border-[#30363d] rounded-md p-4 shadow-sm space-y-3.5">
      <div className="flex items-center justify-between border-b border-[#30363d] pb-2.5">
        <h3 className="text-xs font-semibold text-[#e6edf3] flex items-center space-x-2">
          <GitPullRequest className="w-4 h-4 text-[#848d97]" />
          <span>Audit Review Findings &amp; Heuristics</span>
        </h3>
        <span className="text-[11px] text-[#848d97] font-mono">
          Deterministic Engine
        </span>
      </div>

      <div className="space-y-3">
        {/* Imperative Mood Actionable Suggestion - Styled like GitHub PR Suggested Change */}
        <div className="rounded-md border border-[#30363d] bg-[#0d1117] overflow-hidden">
          <div className="bg-[#161b22] px-3 py-2 border-b border-[#30363d] flex items-center justify-between">
            <span className="text-xs font-semibold text-[#e6edf3] flex items-center space-x-1.5">
              {imp.is_imperative ? (
                <CheckCircle2 className="w-3.5 h-3.5 text-[#3fb950]" />
              ) : (
                <AlertTriangle className="w-3.5 h-3.5 text-[#d29922]" />
              )}
              <span>Imperative Mood Syntax Check</span>
            </span>
            <span
              className={`text-[10px] font-mono px-2 py-0.5 rounded border font-semibold ${
                imp.is_imperative
                  ? 'text-[#3fb950] bg-[#238636]/15 border-[#238636]/40'
                  : 'text-[#d29922] bg-[#bb8009]/15 border-[#bb8009]/40'
              }`}
            >
              {imp.status}
            </span>
          </div>

          <div className="p-3 space-y-2.5">
            <p className="text-xs text-[#848d97] leading-relaxed">
              {imp.evidence}
            </p>

            {imp.suggestion && (
              <div className="rounded-md border border-[#30363d] bg-[#0d1117] overflow-hidden">
                <div className="bg-[#161b22] px-3 py-1.5 border-b border-[#30363d] text-[11px] font-semibold text-[#848d97]">
                  Suggested change
                </div>
                <div className="font-mono text-xs p-2.5 space-y-1">
                  <div className="bg-[#da3633]/15 text-[#e6edf3] px-2 py-0.5 rounded-sm flex items-center space-x-2">
                    <span className="text-[#f85149] select-none">-</span>
                    <span className="line-through opacity-80">{commit_message}</span>
                  </div>
                  <div className="bg-[#2ea043]/15 text-[#e6edf3] px-2 py-0.5 rounded-sm flex items-center space-x-2">
                    <span className="text-[#3fb950] select-none">+</span>
                    <span className="font-semibold text-[#3fb950]">{imp.suggestion}</span>
                  </div>
                </div>

                <div className="p-2 bg-[#161b22] border-t border-[#30363d] flex justify-end">
                  <button
                    onClick={() => onApplyImperativeSuggestion(imp.suggestion!)}
                    className="px-3 py-1 rounded-md bg-[#238636] hover:bg-[#2ea043] text-white font-medium text-xs flex items-center space-x-1.5 transition cursor-pointer shadow-sm"
                  >
                    <Check className="w-3.5 h-3.5" />
                    <span>Apply suggestion</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Type Match Matrix Finding */}
        <div className="p-3 rounded-md bg-[#0d1117] border border-[#30363d] space-y-1.5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-[#e6edf3] flex items-center space-x-1.5">
              <GitCommit className="w-3.5 h-3.5 text-[#848d97]" />
              <span>Conventional Commit Type Agreement</span>
            </span>
            <span
              className={`text-[10px] font-mono px-2 py-0.5 rounded border font-semibold ${
                typeMatch.status === 'PASS'
                  ? 'text-[#3fb950] bg-[#238636]/15 border-[#238636]/40'
                  : typeMatch.status === 'WARN'
                  ? 'text-[#d29922] bg-[#bb8009]/15 border-[#bb8009]/40'
                  : typeMatch.status === 'FAIL'
                  ? 'text-[#f85149] bg-[#da3633]/15 border-[#da3633]/40'
                  : 'text-[#848d97] bg-[#21262d] border-[#30363d]'
              }`}
            >
              {typeMatch.status}
            </span>
          </div>

          <p className="text-xs text-[#848d97] leading-relaxed">
            {typeMatch.evidence}
          </p>

          <div className="flex items-center space-x-3 text-[11px] text-[#848d97] pt-1 font-mono">
            <span>Diff inferred: <strong className="text-[#58a6ff]">{typeMatch.diff_inferred_type}</strong></span>
            <span>·</span>
            <span>Message intent: <strong className="text-[#a371f7]">{typeMatch.predicted_message_type}</strong></span>
          </div>
        </div>

        {/* Dynamic Weights Rebalancing */}
        <div className="p-3 rounded-md bg-[#0d1117] border border-[#30363d] text-[11px] text-[#848d97] space-y-1.5">
          <div className="flex items-center space-x-1.5 text-[#e6edf3] font-semibold">
            <SlidersHorizontal className="w-3.5 h-3.5 text-[#848d97]" />
            <span>Active Aggregator Normalization (weights.yaml)</span>
          </div>
          <div className="flex flex-wrap gap-1.5 pt-0.5">
            {Object.entries(aggregation.weights_used).map(([key, weight]) => (
              <span
                key={key}
                className="px-2 py-0.5 rounded bg-[#161b22] border border-[#30363d] text-[#c9d1d9] font-mono text-[10px]"
              >
                {key.replace('_', ' ')}: <strong className="text-[#58a6ff]">{Math.round(weight * 100)}%</strong>
              </span>
            ))}
          </div>
          {aggregation.missing_sub_scores.length > 0 && (
            <div className="text-[10px] text-[#848d97] pt-0.5">
              * Excluded / Neutral dimensions: {aggregation.missing_sub_scores.join(', ')} (remaining weights automatically scaled to sum to 100%).
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
