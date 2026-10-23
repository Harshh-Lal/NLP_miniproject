import { GitPullRequest, GitBranch, CheckCircle2, ShieldAlert, Cpu, Terminal } from 'lucide-react';

export const HeroBanner = () => {
  return (
    <div className="rounded-lg bg-[#161b22] border border-[#30363d] p-5 sm:p-6 mb-6 shadow-sm">
      <div className="max-w-4xl space-y-3.5">
        {/* GitHub PR metadata line */}
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <span className="inline-flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full bg-[#238636]/15 border border-[#238636]/40 text-[#3fb950] font-medium text-[11px]">
            <GitPullRequest className="w-3 h-3" />
            <span>Pre-merge Audit Check</span>
          </span>

          <span className="inline-flex items-center space-x-1.5 px-2 py-0.5 rounded-md bg-[#0d1117] border border-[#30363d] text-[#848d97] font-mono text-[11px]">
            <GitBranch className="w-3 h-3 text-[#848d97]" />
            <span className="text-[#e6edf3]">main</span>
            <span className="text-[#6e7681]">←</span>
            <span className="text-[#58a6ff]">feature/audit-candidate</span>
          </span>

          <span className="text-[#848d97] font-mono text-[11px] hidden sm:inline">
            Deterministic NLP · Zero Hallucinations
          </span>
        </div>

        {/* Title */}
        <h1 className="text-xl sm:text-2xl font-semibold tracking-tight text-[#e6edf3] leading-snug">
          Semantic Git Commit &amp; PR Consistency Auditor
        </h1>

        {/* Subtitle */}
        <p className="text-xs sm:text-sm text-[#848d97] leading-relaxed max-w-3xl">
          Verifies whether commit messages truthfully reflect source diffs using Part-of-Speech 
          imperative mood verification, AST-extracted symbol coverage, conventional commit classification, 
          and sensitive architecture boundary guards.
        </p>

        {/* GitHub Checks summary pill grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 pt-2">
          <div className="px-3 py-2 rounded-md bg-[#0d1117] border border-[#30363d] flex flex-col justify-between">
            <span className="text-[10px] text-[#848d97] uppercase font-mono tracking-wider">Imperative Mood</span>
            <div className="text-xs font-semibold text-[#3fb950] mt-1 flex items-center space-x-1.5">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>CO2 POS Tagger</span>
            </div>
          </div>

          <div className="px-3 py-2 rounded-md bg-[#0d1117] border border-[#30363d] flex flex-col justify-between">
            <span className="text-[10px] text-[#848d97] uppercase font-mono tracking-wider">Symbol Coverage</span>
            <div className="text-xs font-semibold text-[#58a6ff] mt-1 flex items-center space-x-1.5">
              <Cpu className="w-3.5 h-3.5" />
              <span>Diff AST Matcher</span>
            </div>
          </div>

          <div className="px-3 py-2 rounded-md bg-[#0d1117] border border-[#30363d] flex flex-col justify-between">
            <span className="text-[10px] text-[#848d97] uppercase font-mono tracking-wider">Security Boundary</span>
            <div className="text-xs font-semibold text-[#d29922] mt-1 flex items-center space-x-1.5">
              <ShieldAlert className="w-3.5 h-3.5" />
              <span>Layer Boundary Rule</span>
            </div>
          </div>

          <div className="px-3 py-2 rounded-md bg-[#0d1117] border border-[#30363d] flex flex-col justify-between">
            <span className="text-[10px] text-[#848d97] uppercase font-mono tracking-wider">Pipeline Latency</span>
            <div className="text-xs font-mono font-medium text-[#e6edf3] mt-1 flex items-center space-x-1.5">
              <Terminal className="w-3.5 h-3.5 text-[#848d97]" />
              <span>&lt; 5 ms per commit</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
