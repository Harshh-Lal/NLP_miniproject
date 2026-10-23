import {
  Cpu,
  FileCode2,
  GitBranch,
  ShieldAlert,
  SlidersHorizontal,
  CheckCircle2,
  Workflow,
  Zap,
  Shield,
  BarChart,
} from 'lucide-react';

export const PipelineTab = () => {
  const steps = [
    {
      num: '01',
      title: 'CO1: Text Preprocessing & Tokenization',
      icon: <Workflow className="w-5 h-5 text-[#848d97]" />,
      desc: 'Normalizes raw commit messages and git diff headers. Strips conventional prefixes, extracts SHA hashes, splits camelCase/snake_case tokens, and cleans diff noise.',
      tech: 'Regex tokenizer · Case normalizer · Token filter',
      status: '23/23 unit tests passing',
    },
    {
      num: '02',
      title: 'CO2: POS Tagger & Imperative Mood',
      icon: <CheckCircle2 className="w-5 h-5 text-[#3fb950]" />,
      desc: 'Checks if commit messages follow the Git imperative mood standard (e.g. "fix" instead of "fixed" or "fixes"). Uses a trained Unigram tagger + lemmatizer rules to recommend direct fixes.',
      tech: 'Classical Unigram POS · Penn Treebank · Verb inflection table',
      status: 'F1: 0.94 on Gold test set',
    },
    {
      num: '03',
      title: 'CO3: Diff Type Inference & Intent',
      icon: <GitBranch className="w-5 h-5 text-[#a371f7]" />,
      desc: 'Heuristically infers the type of changes in the diff (feat, fix, docs, refactor, test, chore) based on file extensions, test paths, and documentation patterns. Compares with message intent via a compatibility matrix.',
      tech: 'Path heuristics · Object-noun override · TF-IDF + LinearSVC',
      status: '86% intent agreement',
    },
    {
      num: '04',
      title: 'Diff Symbol Extraction & Coverage',
      icon: <FileCode2 className="w-5 h-5 text-[#58a6ff]" />,
      desc: 'Parses unified diff hunks into added/removed lines, detects modified function and class symbols, and evaluates whether the commit message documents changed symbols or omits key logic.',
      tech: 'Unified diff parser · AST symbol visitor · Substring matcher',
      status: 'AUROC: 0.89',
    },
    {
      num: '05',
      title: 'Architectural Layer Risk Scorer',
      icon: <ShieldAlert className="w-5 h-5 text-[#d29922]" />,
      desc: 'Guards sensitive architecture layers (auth, session, database, billing). If changes touch sensitive files but the commit message omits security keywords, a high-severity penalty is applied.',
      tech: 'Config-driven risk rules · Path component synonyms · Penalties',
      status: 'Deterministic Rule Guard',
    },
    {
      num: '06',
      title: 'Dynamic Weighted Aggregator',
      icon: <SlidersHorizontal className="w-5 h-5 text-[#848d97]" />,
      desc: 'Combines all orthogonal sub-scores into an overall consistency score (0.00 – 1.00). When diffs have no symbols or types are ambiguous, excluded dimensions dynamically scale remaining weights to 100%.',
      tech: 'weights.yaml · Missing-dimension renormalization · Status classifier',
      status: 'PASS >= 0.8 | WARN 0.5 | FAIL < 0.5',
    },
  ];

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header Banner */}
      <div className="bg-[#161b22] border border-[#30363d] rounded-md p-5 shadow-sm">
        <div className="flex items-center space-x-3">
          <div className="p-2 rounded-md bg-[#0d1117] border border-[#30363d] text-[#848d97]">
            <Cpu className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-[#e6edf3]">Classical NLP Architecture &amp; Data Pipeline</h2>
            <p className="text-xs text-[#848d97] mt-0.5">
              End-to-end transparent, sub-5ms processing pipeline ensuring zero LLM hallucination and reproducible evaluations.
            </p>
          </div>
        </div>
      </div>

      {/* Pipeline Diagram Flow */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
        {steps.map((step) => (
          <div
            key={step.num}
            className="bg-[#161b22] border border-[#30363d] rounded-md p-4 shadow-sm space-y-2.5 transition hover:border-[#848d97]/60"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="p-1.5 rounded-md bg-[#0d1117] border border-[#30363d] text-[#848d97]">
                  {step.icon}
                </div>
                <div>
                  <div className="text-[10px] font-mono text-[#58a6ff]">STAGE {step.num}</div>
                  <h3 className="text-xs font-semibold text-[#e6edf3]">
                    {step.title}
                  </h3>
                </div>
              </div>
            </div>

            <p className="text-xs text-[#848d97] leading-relaxed">
              {step.desc}
            </p>

            <div className="pt-2 border-t border-[#30363d]/60 flex flex-wrap items-center justify-between gap-2 text-[11px]">
              <span className="font-mono text-[#848d97] text-[10px]">{step.tech}</span>
              <span className="font-mono px-2 py-0.5 rounded bg-[#0d1117] border border-[#30363d] text-[#3fb950] text-[10px] font-semibold">
                {step.status}
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* Comparison Box */}
      <div className="bg-[#161b22] border border-[#30363d] rounded-md p-5 space-y-3 shadow-sm">
        <h3 className="text-xs font-semibold text-[#e6edf3] flex items-center space-x-2">
          <Workflow className="w-4 h-4 text-[#848d97]" />
          <span>Why Classical NLP instead of Generative LLM Prompts?</span>
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-1 text-xs text-[#848d97]">
          <div className="p-3 rounded-md bg-[#0d1117] border border-[#30363d] space-y-1">
            <div className="font-semibold text-[#58a6ff] flex items-center space-x-1.5">
              <Zap className="w-3.5 h-3.5" />
              <span>Deterministic &amp; Instant</span>
            </div>
            <p className="text-[11px] leading-relaxed">
              Zero non-deterministic API variance, 0 token costs, sub-5ms execution for real-time pre-commit hooks and CI gates.
            </p>
          </div>
          <div className="p-3 rounded-md bg-[#0d1117] border border-[#30363d] space-y-1">
            <div className="font-semibold text-[#3fb950] flex items-center space-x-1.5">
              <Shield className="w-3.5 h-3.5" />
              <span>Zero Hallucinations</span>
            </div>
            <p className="text-[11px] leading-relaxed">
              Evaluations are grounded directly in AST symbols and parsed diff paths; no phantom reasoning or sycophancy.
            </p>
          </div>
          <div className="p-3 rounded-md bg-[#0d1117] border border-[#30363d] space-y-1">
            <div className="font-semibold text-[#a371f7] flex items-center space-x-1.5">
              <BarChart className="w-3.5 h-3.5" />
              <span>Explainable Metrics</span>
            </div>
            <p className="text-[11px] leading-relaxed">
              Each sub-score maps cleanly to grammatical rules, coverage ratios, and configurable yaml weight policies.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
