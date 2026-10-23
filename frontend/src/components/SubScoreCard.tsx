import type { ReactNode } from 'react';
import { CheckCircle2, AlertTriangle, XCircle, HelpCircle } from 'lucide-react';

interface SubScoreCardProps {
  title: string;
  score: number | null;
  status: string;
  weightPercent?: number;
  icon: ReactNode;
  evidence: string;
  isAmbiguous?: boolean;
}

export const SubScoreCard = ({
  title,
  score,
  status,
  weightPercent,
  icon,
  evidence,
  isAmbiguous,
}: SubScoreCardProps) => {
  const getStatusBadge = (s: string) => {
    switch (s) {
      case 'PASS':
        return 'text-[#3fb950] bg-[#238636]/15 border-[#238636]/40';
      case 'WARN':
        return 'text-[#d29922] bg-[#bb8009]/15 border-[#bb8009]/40';
      case 'FAIL':
        return 'text-[#f85149] bg-[#da3633]/15 border-[#da3633]/40';
      default:
        return 'text-[#848d97] bg-[#21262d] border-[#30363d]';
    }
  };

  const getStatusIcon = (s: string) => {
    switch (s) {
      case 'PASS':
        return <CheckCircle2 className="w-4 h-4 text-[#3fb950]" />;
      case 'WARN':
        return <AlertTriangle className="w-4 h-4 text-[#d29922]" />;
      case 'FAIL':
        return <XCircle className="w-4 h-4 text-[#f85149]" />;
      default:
        return <HelpCircle className="w-4 h-4 text-[#848d97]" />;
    }
  };

  const getProgressColor = (sc: number | null) => {
    if (sc === null) return 'bg-[#30363d]';
    if (sc >= 0.8) return 'bg-[#238636]';
    if (sc >= 0.5) return 'bg-[#d29922]';
    return 'bg-[#da3633]';
  };

  const percentage = score !== null ? Math.round(score * 100) : null;

  return (
    <div className="bg-[#161b22] border border-[#30363d] rounded-md p-3.5 shadow-sm transition hover:border-[#848d97]/50 space-y-2.5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2.5">
          <div className="p-1.5 rounded-md bg-[#0d1117] border border-[#30363d] text-[#848d97]">
            {icon || getStatusIcon(status)}
          </div>
          <div>
            <h4 className="text-xs font-semibold text-[#e6edf3]">{title}</h4>
            {weightPercent !== undefined && (
              <span className="text-[10px] text-[#848d97] font-mono">Weight: {weightPercent}%</span>
            )}
          </div>
        </div>

        <div className="flex items-center space-x-2">
          {isAmbiguous && (
            <span className="text-[10px] px-1.5 py-0.2 rounded border font-semibold text-[#d29922] bg-[#bb8009]/15 border-[#bb8009]/40 font-mono">
              AMBIGUOUS
            </span>
          )}
          <span className={`text-[10px] font-mono font-semibold px-2 py-0.5 rounded border ${getStatusBadge(status)}`}>
            {status}
          </span>
          <span className="text-sm font-mono font-semibold text-[#e6edf3] min-w-9 text-right">
            {score !== null ? score.toFixed(2) : 'N/A'}
          </span>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="w-full h-1.5 rounded-full bg-[#0d1117] border border-[#30363d]/50 overflow-hidden">
        <div
          className={`h-full transition-all duration-500 ${getProgressColor(score)}`}
          style={{ width: `${percentage !== null ? percentage : 0}%` }}
        />
      </div>

      {/* Evidence summary */}
      <p className="text-[11px] text-[#848d97] leading-relaxed">
        {evidence}
      </p>
    </div>
  );
};
