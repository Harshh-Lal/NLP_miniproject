import { ShieldAlert, ShieldCheck, AlertTriangle } from 'lucide-react';
import type { SubScoreRisk } from '../types';

interface RiskAlertCardProps {
  risk: SubScoreRisk;
}

export const RiskAlertCard = ({ risk }: RiskAlertCardProps) => {
  const hasFlags = risk.flags && risk.flags.length > 0;

  return (
    <div
      className={`rounded-md p-4 shadow-sm border transition-all ${
        hasFlags
          ? 'bg-[#da3633]/10 border-[#da3633]/40 border-l-4 border-l-[#f85149]'
          : 'bg-[#161b22] border-[#30363d]'
      }`}
    >
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center space-x-2">
          <div
            className={`p-1.5 rounded-md border ${
              hasFlags
                ? 'bg-[#da3633]/20 text-[#f85149] border-[#da3633]/40'
                : 'bg-[#0d1117] text-[#3fb950] border-[#30363d]'
            }`}
          >
            {hasFlags ? <ShieldAlert className="w-4 h-4" /> : <ShieldCheck className="w-4 h-4" />}
          </div>
          <div>
            <h4 className="text-xs font-semibold text-[#e6edf3]">
              Architectural Boundary &amp; Security Safety
            </h4>
            <span className="text-[10px] text-[#848d97] font-mono">
              {risk.layers_triggered?.length || 0} sensitive layers monitored
            </span>
          </div>
        </div>

        <span
          className={`text-[10px] font-mono font-semibold px-2 py-0.5 rounded border ${
            risk.status === 'PASS'
              ? 'text-[#3fb950] bg-[#238636]/15 border-[#238636]/40'
              : risk.status === 'WARN'
              ? 'text-[#d29922] bg-[#bb8009]/15 border-[#bb8009]/40'
              : 'text-[#f85149] bg-[#da3633]/15 border-[#da3633]/40'
          }`}
        >
          {risk.status}
        </span>
      </div>

      <p className="text-[11px] text-[#848d97] leading-relaxed mb-2">
        {risk.evidence}
      </p>

      {hasFlags ? (
        <div className="space-y-2 mt-2.5 pt-2 border-t border-[#da3633]/30">
          <div className="text-[10px] font-semibold text-[#f85149] uppercase tracking-wider flex items-center space-x-1.5">
            <AlertTriangle className="w-3 h-3 text-[#f85149]" />
            <span>Violations &amp; Unmentioned Sensitive Files</span>
          </div>
          <ul className="space-y-1.5">
            {risk.flags.map((flag, idx) => (
              <li
                key={idx}
                className="p-2.5 rounded bg-[#0d1117] border border-[#da3633]/30 text-[#f85149] text-xs font-mono leading-relaxed"
              >
                {flag}
              </li>
            ))}
          </ul>
        </div>
      ) : (
        <div className="text-[11px] text-[#3fb950] font-medium flex items-center space-x-1.5 pt-1">
          <ShieldCheck className="w-3.5 h-3.5 shrink-0" />
          <span>All modified files conform to safe architectural boundaries without unmentioned security layer changes.</span>
        </div>
      )}
    </div>
  );
};
