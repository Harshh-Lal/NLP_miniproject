import { ShieldAlert, Table, SlidersHorizontal } from 'lucide-react';

export const RuleMatrixTab = () => {
  const sensitiveLayers = [
    {
      layer: 'Authentication & Security',
      severity: 'HIGH',
      penalty: '0.50 Penalty',
      paths: ['auth', 'authentication', 'security', 'session', 'oauth', 'permission', 'token', 'crypto', 'login'],
      synonyms: ['credential', 'password', 'jwt', 'oauth', 'token', 'session', 'login'],
      warning: 'Modifying security files without mentioning auth/token keywords triggers immediate security risk flag.',
    },
    {
      layer: 'Database & Migrations',
      severity: 'MEDIUM',
      penalty: '0.30 Penalty',
      paths: ['migration', 'migrations', 'schema', 'db', 'database', 'alembic'],
      synonyms: ['table', 'tables', 'column', 'sql', 'schema', 'db', 'database', 'migration'],
      warning: 'Database schema migrations require explicit database/migration references in the commit message.',
    },
    {
      layer: 'Billing & Financial',
      severity: 'HIGH',
      penalty: '0.50 Penalty',
      paths: ['billing', 'payment', 'payments', 'checkout', 'stripe', 'paypal', 'invoice'],
      synonyms: ['subscription', 'refund', 'invoice', 'payment', 'checkout', 'stripe'],
      warning: 'Billing code modifications without financial keywords triggers a high-severity consistency violation.',
    },
  ];

  const types = ['feat', 'fix', 'refactor', 'test', 'chore', 'docs'];
  const matrix: Record<string, Record<string, number>> = {
    feat: { feat: 1.0, fix: 0.0, refactor: 0.5, test: 0.5, chore: 0.5, docs: 0.0 },
    fix: { feat: 0.0, fix: 1.0, refactor: 0.5, test: 0.5, chore: 0.3, docs: 0.0 },
    refactor: { feat: 0.5, fix: 0.5, refactor: 1.0, test: 0.5, chore: 0.5, docs: 0.0 },
    test: { feat: 0.5, fix: 0.5, refactor: 0.5, test: 1.0, chore: 0.5, docs: 0.0 },
    chore: { feat: 0.5, fix: 0.0, refactor: 0.5, test: 0.5, chore: 1.0, docs: 0.5 },
    docs: { feat: 0.0, fix: 0.0, refactor: 0.0, test: 0.0, chore: 0.5, docs: 1.0 },
  };

  const getCellColor = (val: number) => {
    if (val === 1.0) return 'bg-[#238636]/20 text-[#3fb950] font-semibold';
    if (val >= 0.5) return 'bg-[#388bfd]/20 text-[#58a6ff] font-medium';
    if (val > 0) return 'bg-[#bb8009]/20 text-[#d29922]';
    return 'bg-[#0d1117] text-[#6e7681]';
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="bg-[#161b22] border border-[#30363d] rounded-md p-5 shadow-sm">
        <div className="flex items-center space-x-3">
          <div className="p-2 rounded-md bg-[#0d1117] border border-[#30363d] text-[#848d97]">
            <SlidersHorizontal className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-[#e6edf3]">Rule Engine &amp; Configuration Matrix</h2>
            <p className="text-xs text-[#848d97] mt-0.5">
              YAML-governed policies for architectural boundary risk, conventional commit type compatibility, and sub-score weighting.
            </p>
          </div>
        </div>
      </div>

      {/* Weights Overview */}
      <div className="bg-[#161b22] border border-[#30363d] rounded-md p-5 shadow-sm space-y-3">
        <h3 className="text-xs font-semibold text-[#e6edf3] flex items-center space-x-2">
          <SlidersHorizontal className="w-4 h-4 text-[#848d97]" />
          <span>Sub-Score Aggregation Weights (weights.yaml)</span>
        </h3>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 text-center">
          <div className="p-3 rounded-md bg-[#0d1117] border border-[#30363d]">
            <div className="text-xl font-bold font-mono text-[#58a6ff]">35%</div>
            <div className="text-xs text-[#e6edf3] font-medium mt-1">Symbol Coverage</div>
            <div className="text-[10px] text-[#848d97]">AST Function &amp; Class Mentions</div>
          </div>
          <div className="p-3 rounded-md bg-[#0d1117] border border-[#30363d]">
            <div className="text-xl font-bold font-mono text-[#3fb950]">25%</div>
            <div className="text-xs text-[#e6edf3] font-medium mt-1">Imperative Mood</div>
            <div className="text-[10px] text-[#848d97]">Git Convention Grammar</div>
          </div>
          <div className="p-3 rounded-md bg-[#0d1117] border border-[#30363d]">
            <div className="text-xl font-bold font-mono text-[#d29922]">20%</div>
            <div className="text-xs text-[#e6edf3] font-medium mt-1">Risk Safety</div>
            <div className="text-[10px] text-[#848d97]">Sensitive Boundary Rules</div>
          </div>
          <div className="p-3 rounded-md bg-[#0d1117] border border-[#30363d]">
            <div className="text-xl font-bold font-mono text-[#a371f7]">20%</div>
            <div className="text-xs text-[#e6edf3] font-medium mt-1">Type Consistency</div>
            <div className="text-[10px] text-[#848d97]">Diff vs Message Intent</div>
          </div>
        </div>
      </div>

      {/* Type Compatibility Matrix */}
      <div className="bg-[#161b22] border border-[#30363d] rounded-md p-5 shadow-sm space-y-3 overflow-hidden">
        <h3 className="text-xs font-semibold text-[#e6edf3] flex items-center space-x-2">
          <Table className="w-4 h-4 text-[#848d97]" />
          <span>Conventional Commit Type Compatibility Matrix (type_compatibility.yaml)</span>
        </h3>
        <p className="text-xs text-[#848d97]">
          Compares inferred diff type (vertical) with stated message intent (horizontal). Exact matches receive 1.00; related cross-functional workflows receive partial credit (0.50).
        </p>
        <div className="overflow-x-auto pt-2">
          <table className="w-full text-center border-collapse text-xs font-mono border border-[#30363d] rounded-md overflow-hidden">
            <thead>
              <tr className="border-b border-[#30363d] bg-[#0d1117] text-[#848d97]">
                <th className="p-2.5 text-left text-[11px] font-sans font-semibold border-r border-[#30363d]">Diff \ Msg</th>
                {types.map((t) => (
                  <th key={t} className="p-2.5 text-[11px] uppercase font-bold text-[#e6edf3]">{t}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {types.map((rowType) => (
                <tr key={rowType} className="border-b border-[#30363d]/60">
                  <td className="p-2 text-left font-bold text-[#e6edf3] uppercase bg-[#0d1117] border-r border-[#30363d]">{rowType}</td>
                  {types.map((colType) => {
                    const val = matrix[rowType]?.[colType] ?? 0;
                    return (
                      <td key={colType} className={`p-2 transition ${getCellColor(val)}`}>
                        {val.toFixed(1)}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Sensitive Layer Rules */}
      <div className="bg-[#161b22] border border-[#30363d] rounded-md p-5 shadow-sm space-y-3.5">
        <h3 className="text-xs font-semibold text-[#e6edf3] flex items-center space-x-2">
          <ShieldAlert className="w-4 h-4 text-[#d29922]" />
          <span>Monitored Sensitive Architectural Layers (risk_rules.yaml)</span>
        </h3>

        <div className="space-y-2.5">
          {sensitiveLayers.map((layer) => (
            <div
              key={layer.layer}
              className="p-3.5 rounded-md bg-[#0d1117] border border-[#30363d] space-y-2"
            >
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center space-x-2">
                  <span className="font-semibold text-xs text-[#e6edf3]">{layer.layer}</span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-[#bb8009]/15 border border-[#bb8009]/40 text-[#d29922]">
                    {layer.severity}
                  </span>
                </div>
                <span className="text-xs font-mono text-[#f85149] font-semibold">{layer.penalty}</span>
              </div>

              <div className="text-[11px] text-[#848d97]">
                <strong>Path Keywords:</strong>{' '}
                <span className="font-mono text-[#c9d1d9]">{layer.paths.join(', ')}</span>
              </div>
              <div className="text-[11px] text-[#848d97]">
                <strong>Message Synonyms:</strong>{' '}
                <span className="font-mono text-[#58a6ff]">{layer.synonyms.join(', ')}</span>
              </div>
              <p className="text-[11px] text-[#848d97] italic pt-1 border-t border-[#30363d]/60">
                {layer.warning}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
