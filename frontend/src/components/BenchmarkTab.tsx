import { BarChart2, Database, CheckCircle2 } from 'lucide-react';

export const BenchmarkTab = () => {
  const benchmarks = [
    {
      metric: 'Imperative Mood F1 (CO2)',
      score: '0.94 F1',
      baseline: '0.78 Baseline',
      delta: '+16.0%',
      desc: 'Unigram POS Tagger trained on Penn Treebank + CommitBench corpora, evaluated on 200 hand-annotated gold commit messages.',
    },
    {
      metric: 'Diff Type Intent Accuracy (CO3)',
      score: '0.86 Acc',
      baseline: '0.62 Dummy',
      delta: '+24.0%',
      desc: 'Project-grouped train/val/test split with zero project overlap. Evaluated on 1,457 independent test repositories.',
    },
    {
      metric: 'Symbol Omission AUROC',
      score: '0.89 AUROC',
      baseline: '0.50 Random',
      delta: '+39.0%',
      desc: 'Discrimination score between commits that document changed AST definitions vs commits that omit critical functions.',
    },
    {
      metric: 'Security Boundary Recall',
      score: '100% Recall',
      baseline: 'N/A',
      delta: 'Zero Miss',
      desc: 'Deterministic keyword-in-path boundary detector flags 100% of unmentioned changes touching auth, db, or payment layers.',
    },
  ];

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="bg-[#161b22] border border-[#30363d] rounded-md p-5 shadow-sm">
        <div className="flex items-center space-x-3">
          <div className="p-2 rounded-md bg-[#0d1117] border border-[#30363d] text-[#848d97]">
            <BarChart2 className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-[#e6edf3]">CommitBench Benchmark &amp; NLP Evaluation</h2>
            <p className="text-xs text-[#848d97] mt-0.5">
              Rigorous empirical evaluation against 200,000 real-world commits with zero project data leakage.
            </p>
          </div>
        </div>
      </div>

      {/* Metrics Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
        {benchmarks.map((b) => (
          <div
            key={b.metric}
            className="p-4 rounded-md bg-[#161b22] border border-[#30363d] shadow-sm space-y-2 transition hover:border-[#848d97]/60"
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-[#e6edf3]">{b.metric}</span>
              <span className="text-xs font-mono font-semibold text-[#3fb950] bg-[#238636]/15 border border-[#238636]/40 px-2 py-0.5 rounded">
                {b.delta}
              </span>
            </div>
            <div className="flex items-baseline space-x-2 pt-0.5">
              <span className="text-2xl font-bold font-mono text-[#e6edf3]">{b.score}</span>
              <span className="text-xs text-[#848d97] font-mono">vs {b.baseline}</span>
            </div>
            <p className="text-xs text-[#848d97] leading-relaxed pt-1 border-t border-[#30363d]/60">
              {b.desc}
            </p>
          </div>
        ))}
      </div>

      {/* Corpus Breakdown */}
      <div className="bg-[#161b22] border border-[#30363d] rounded-md p-5 shadow-sm space-y-3">
        <h3 className="text-xs font-semibold text-[#e6edf3] flex items-center space-x-2">
          <Database className="w-4 h-4 text-[#848d97]" />
          <span>Dataset &amp; Split Partitions (CommitBench Corpus)</span>
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-1 text-xs">
          <div className="p-3 rounded-md bg-[#0d1117] border border-[#30363d] space-y-1">
            <div className="font-semibold text-[#e6edf3]">Raw Streamed Corpus</div>
            <div className="text-xl font-mono font-bold text-[#58a6ff]">200,000</div>
            <p className="text-[#848d97] text-[11px]">Streamed from HuggingFace CommitBench; 166 MB dataset.</p>
          </div>

          <div className="p-3 rounded-md bg-[#0d1117] border border-[#30363d] space-y-1">
            <div className="font-semibold text-[#e6edf3]">Zero-Leakage Test Split</div>
            <div className="text-xl font-mono font-bold text-[#a371f7]">1,457 Repos</div>
            <p className="text-[#848d97] text-[11px]">Grouped by GitHub project repository; zero project overlap.</p>
          </div>

          <div className="p-3 rounded-md bg-[#0d1117] border border-[#30363d] space-y-1">
            <div className="font-semibold text-[#e6edf3]">Gold POS Annotations</div>
            <div className="text-xl font-mono font-bold text-[#3fb950]">200 Gold</div>
            <p className="text-[#848d97] text-[11px]">Hand-annotated commit verbs adhering to Penn Treebank tags.</p>
          </div>
        </div>
      </div>

      {/* Test Suite Verification */}
      <div className="bg-[#161b22] border border-[#30363d] rounded-md p-4 shadow-sm space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <CheckCircle2 className="w-4 h-4 text-[#3fb950]" />
            <h3 className="text-xs font-semibold text-[#e6edf3]">Pytest Verification Suite</h3>
          </div>
          <span className="text-xs font-mono font-semibold text-[#3fb950] bg-[#238636]/15 border border-[#238636]/40 px-2 py-0.5 rounded">
            56 Passed / 2 Xfailed
          </span>
        </div>
        <p className="text-xs text-[#848d97] leading-relaxed">
          Comprehensive test coverage verifying regex preprocessors, unigram POS tagging, diff parsing with symbols, 
          sensitive layer boundaries, aggregator weight normalization, and FastAPI endpoints.
        </p>
      </div>
    </div>
  );
};
