import {
  GitPullRequest,
  Cpu,
  SlidersHorizontal,
  BarChart2,
  ExternalLink,
} from 'lucide-react';

const GithubIcon = ({ className = 'w-4 h-4' }: { className?: string }) => (
  <svg viewBox="0 0 24 24" fill="currentColor" className={className} aria-hidden="true">
    <path fillRule="evenodd" clipRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" />
  </svg>
);

interface NavbarProps {
  activeTab: 'auditor' | 'pipeline' | 'rules' | 'benchmarks';
  setActiveTab: (tab: 'auditor' | 'pipeline' | 'rules' | 'benchmarks') => void;
  apiHealthy: boolean;
  onRefreshHealth: () => void;
}

export const Navbar = ({ activeTab, setActiveTab, apiHealthy, onRefreshHealth }: NavbarProps) => {
  return (
    <header className="border-b border-[#30363d] bg-[#161b22] sticky top-0 z-30 transition-all select-none">
      <div className="max-w-7xl mx-auto px-4 sm:px-6">
        {/* Top Header Row */}
        <div className="h-14 flex items-center justify-between gap-3">
          {/* Brand & Repo Breadcrumb */}
          <div
            className="flex items-center space-x-2.5 cursor-pointer"
            onClick={() => setActiveTab('auditor')}
          >
            <div className="w-8 h-8 rounded-md bg-[#21262d] border border-[#30363d] flex items-center justify-center text-[#e6edf3] hover:border-[#848d97] transition">
              <GithubIcon className="w-5 h-5 text-[#e6edf3]" />
            </div>

            <div className="flex items-center space-x-1.5 text-sm">
              <span className="text-[#848d97] hover:text-[#58a6ff] transition font-normal">
                codereviewer
              </span>
              <span className="text-[#6e7681]">/</span>
              <span className="font-semibold text-[#e6edf3] tracking-tight hover:text-[#58a6ff] transition">
                consistency-auditor
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full border border-[#30363d] bg-[#0d1117] text-[#848d97] font-medium ml-1">
                Public
              </span>
            </div>
          </div>

          {/* Right Status & Tools */}
          <div className="flex items-center space-x-2 sm:space-x-3">
            <button
              onClick={onRefreshHealth}
              title={apiHealthy ? 'Backend API online on port 8000' : 'Backend API offline. Click to recheck.'}
              className={`text-xs px-2.5 py-1 rounded-md border flex items-center space-x-1.5 transition cursor-pointer font-mono ${
                apiHealthy
                  ? 'bg-[#238636]/15 text-[#3fb950] border-[#238636]/40 hover:bg-[#238636]/25'
                  : 'bg-[#bb8009]/15 text-[#d29922] border-[#bb8009]/40 hover:bg-[#bb8009]/25'
              }`}
            >
              {apiHealthy ? (
                <>
                  <span className="w-2 h-2 rounded-full bg-[#3fb950] animate-pulse" />
                  <span className="text-[11px] font-medium hidden sm:inline">api:8000 online</span>
                  <span className="text-[11px] font-medium sm:hidden">online</span>
                </>
              ) : (
                <>
                  <span className="w-2 h-2 rounded-full bg-[#d29922]" />
                  <span className="text-[11px] font-medium hidden sm:inline">local simulation</span>
                  <span className="text-[11px] font-medium sm:hidden">offline</span>
                </>
              )}
            </button>

            <a
              href="https://github.com"
              target="_blank"
              rel="noreferrer"
              className="px-2.5 py-1 rounded-md bg-[#21262d] hover:bg-[#30363d] text-[#c9d1d9] border border-[#30363d] transition text-xs flex items-center space-x-1"
            >
              <span>Repo</span>
              <ExternalLink className="w-3 h-3 text-[#848d97]" />
            </a>
          </div>
        </div>

        {/* GitHub Repository-style Underline Tabs */}
        <nav className="hidden md:flex items-center space-x-1 border-t border-[#30363d]/60 -mb-[1px]">
          <button
            onClick={() => setActiveTab('auditor')}
            className={`px-3.5 py-2.5 text-xs font-medium transition flex items-center space-x-2 border-b-2 cursor-pointer ${
              activeTab === 'auditor'
                ? 'border-[#f78166] text-[#e6edf3] font-semibold'
                : 'border-transparent text-[#848d97] hover:text-[#e6edf3] hover:border-[#848d97]/40'
            }`}
          >
            <GitPullRequest className="w-4 h-4 text-[#848d97]" />
            <span>Auditor Studio</span>
            <span className="text-[10px] font-mono px-1.5 py-0.2 rounded-full bg-[#30363d] text-[#848d97]">
              Live
            </span>
          </button>

          <button
            onClick={() => setActiveTab('pipeline')}
            className={`px-3.5 py-2.5 text-xs font-medium transition flex items-center space-x-2 border-b-2 cursor-pointer ${
              activeTab === 'pipeline'
                ? 'border-[#f78166] text-[#e6edf3] font-semibold'
                : 'border-transparent text-[#848d97] hover:text-[#e6edf3] hover:border-[#848d97]/40'
            }`}
          >
            <Cpu className="w-4 h-4 text-[#848d97]" />
            <span>NLP Pipeline</span>
            <span className="text-[10px] font-mono px-1.5 py-0.2 rounded-full bg-[#30363d] text-[#848d97]">
              6 Stages
            </span>
          </button>

          <button
            onClick={() => setActiveTab('rules')}
            className={`px-3.5 py-2.5 text-xs font-medium transition flex items-center space-x-2 border-b-2 cursor-pointer ${
              activeTab === 'rules'
                ? 'border-[#f78166] text-[#e6edf3] font-semibold'
                : 'border-transparent text-[#848d97] hover:text-[#e6edf3] hover:border-[#848d97]/40'
            }`}
          >
            <SlidersHorizontal className="w-4 h-4 text-[#848d97]" />
            <span>Rule Matrix</span>
          </button>

          <button
            onClick={() => setActiveTab('benchmarks')}
            className={`px-3.5 py-2.5 text-xs font-medium transition flex items-center space-x-2 border-b-2 cursor-pointer ${
              activeTab === 'benchmarks'
                ? 'border-[#f78166] text-[#e6edf3] font-semibold'
                : 'border-transparent text-[#848d97] hover:text-[#e6edf3] hover:border-[#848d97]/40'
            }`}
          >
            <BarChart2 className="w-4 h-4 text-[#848d97]" />
            <span>CommitBench Evaluation</span>
          </button>
        </nav>
      </div>

      {/* Mobile Nav */}
      <div className="md:hidden flex items-center justify-around border-t border-[#30363d] px-2 py-1.5 bg-[#0d1117] overflow-x-auto text-[11px]">
        <button
          onClick={() => setActiveTab('auditor')}
          className={`px-2.5 py-1 rounded-md font-medium shrink-0 ${
            activeTab === 'auditor' ? 'text-[#e6edf3] bg-[#21262d] font-semibold' : 'text-[#848d97]'
          }`}
        >
          Studio
        </button>
        <button
          onClick={() => setActiveTab('pipeline')}
          className={`px-2.5 py-1 rounded-md font-medium shrink-0 ${
            activeTab === 'pipeline' ? 'text-[#e6edf3] bg-[#21262d] font-semibold' : 'text-[#848d97]'
          }`}
        >
          Pipeline
        </button>
        <button
          onClick={() => setActiveTab('rules')}
          className={`px-2.5 py-1 rounded-md font-medium shrink-0 ${
            activeTab === 'rules' ? 'text-[#e6edf3] bg-[#21262d] font-semibold' : 'text-[#848d97]'
          }`}
        >
          Rule Matrix
        </button>
        <button
          onClick={() => setActiveTab('benchmarks')}
          className={`px-2.5 py-1 rounded-md font-medium shrink-0 ${
            activeTab === 'benchmarks' ? 'text-[#e6edf3] bg-[#21262d] font-semibold' : 'text-[#848d97]'
          }`}
        >
          Benchmarks
        </button>
      </div>
    </header>
  );
};
