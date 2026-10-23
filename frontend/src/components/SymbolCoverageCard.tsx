import { Code2, Check, AlertCircle, Plus } from 'lucide-react';
import type { SubScoreCoverage } from '../types';

interface SymbolCoverageCardProps {
  coverage: SubScoreCoverage;
  onAddSymbolToMessage: (symbol: string) => void;
}

export const SymbolCoverageCard = ({ coverage, onAddSymbolToMessage }: SymbolCoverageCardProps) => {
  const { mentioned_symbols, omitted_symbols, total_symbols, evidence } = coverage;

  return (
    <div className="bg-[#161b22] border border-[#30363d] rounded-md p-4 shadow-sm space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <div className="p-1.5 rounded-md bg-[#0d1117] border border-[#30363d] text-[#848d97]">
            <Code2 className="w-4 h-4" />
          </div>
          <div>
            <h4 className="text-xs font-semibold text-[#e6edf3]">
              AST Changed Symbol Coverage
            </h4>
            <span className="text-[10px] text-[#848d97] font-mono">
              {mentioned_symbols.length} of {total_symbols} symbols documented ({total_symbols > 0 ? Math.round((mentioned_symbols.length / total_symbols) * 100) : 100}%)
            </span>
          </div>
        </div>

        <span
          className={`text-[10px] font-mono font-semibold px-2 py-0.5 rounded border ${
            coverage.status === 'PASS'
              ? 'text-[#3fb950] bg-[#238636]/15 border-[#238636]/40'
              : coverage.status === 'WARN'
              ? 'text-[#d29922] bg-[#bb8009]/15 border-[#bb8009]/40'
              : 'text-[#848d97] bg-[#21262d] border-[#30363d]'
          }`}
        >
          {coverage.status}
        </span>
      </div>

      <p className="text-[11px] text-[#848d97] leading-relaxed">
        {evidence}
      </p>

      {total_symbols > 0 ? (
        <div className="space-y-2.5 pt-1">
          {/* Mentioned Symbols */}
          {mentioned_symbols.length > 0 && (
            <div>
              <div className="text-[10px] font-semibold text-[#3fb950] uppercase tracking-wider mb-1.5 flex items-center space-x-1">
                <Check className="w-3 h-3" />
                <span>Mentioned in Commit Message ({mentioned_symbols.length})</span>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {mentioned_symbols.map((symbol) => (
                  <span
                    key={symbol}
                    className="px-2.5 py-0.5 rounded-full bg-[#238636]/15 border border-[#238636]/40 text-[#3fb950] font-mono text-[11px] flex items-center space-x-1"
                  >
                    <span>✓</span>
                    <span>{symbol}</span>
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Omitted Symbols */}
          {omitted_symbols.length > 0 && (
            <div>
              <div className="text-[10px] font-semibold text-[#f85149] uppercase tracking-wider mb-1.5 flex items-center space-x-1">
                <AlertCircle className="w-3 h-3" />
                <span>Omitted from Message ({omitted_symbols.length})</span>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {omitted_symbols.map((symbol) => (
                  <button
                    key={symbol}
                    onClick={() => onAddSymbolToMessage(symbol)}
                    title={`Click to append "${symbol}" to commit message`}
                    className="px-2.5 py-0.5 rounded-full bg-[#da3633]/15 hover:bg-[#da3633]/25 border border-[#da3633]/40 text-[#f85149] font-mono text-[11px] flex items-center space-x-1.5 transition cursor-pointer group"
                  >
                    <span>✗ {symbol}</span>
                    <span className="text-[10px] bg-[#da3633]/30 group-hover:bg-[#da3633]/50 px-1 py-0.2 rounded text-white flex items-center">
                      <Plus className="w-2.5 h-2.5 mr-0.5" /> Append
                    </span>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="text-[11px] text-[#848d97] italic bg-[#0d1117] p-2 rounded-md border border-[#30363d]">
          No function or class symbols extracted from diff hunks.
        </div>
      )}
    </div>
  );
};
