import { PRESETS } from '../presets';
import type { CommitPreset } from '../types';
import { GitCommit, RotateCcw, ArrowRight } from 'lucide-react';

interface PresetBarProps {
  currentPresetId: string | null;
  onSelectPreset: (preset: CommitPreset) => void;
  onClear: () => void;
}

const PRESET_SHAS: Record<string, string> = {
  'clean-feature': 'c4b18e2',
  'past-tense-fix': '89a0f31',
  'silent-security-risk': '2f71dc0',
  'symbol-omission': '6b50e4a',
  'clean-docs': '9a13b5d',
};

export const PresetBar = ({ currentPresetId, onSelectPreset, onClear }: PresetBarProps) => {
  return (
    <div className="bg-[#161b22] border border-[#30363d] rounded-lg p-4 mb-6 shadow-sm">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-3">
        <div className="flex items-center space-x-2">
          <GitCommit className="w-4 h-4 text-[#848d97]" />
          <span className="text-xs font-semibold text-[#e6edf3]">
            Sample Commit Scenarios
          </span>
          <span className="text-[11px] text-[#848d97] hidden sm:inline">
            — Select a real git commit to evaluate the NLP consistency pipeline
          </span>
        </div>

        <button
          onClick={onClear}
          className="self-start sm:self-auto text-xs px-2.5 py-1 rounded-md bg-[#21262d] hover:bg-[#30363d] text-[#c9d1d9] border border-[#30363d] flex items-center space-x-1.5 transition cursor-pointer"
        >
          <RotateCcw className="w-3 h-3 text-[#848d97]" />
          <span>Reset Input</span>
        </button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-2.5">
        {PRESETS.map((preset) => {
          const isSelected = currentPresetId === preset.id;
          const sha = PRESET_SHAS[preset.id] || '7a8f10b';
          return (
            <button
              key={preset.id}
              onClick={() => onSelectPreset(preset)}
              className={`p-3 rounded-md border text-left transition-all relative flex flex-col justify-between group cursor-pointer ${
                isSelected
                  ? 'bg-[#21262d] border-[#58a6ff] ring-1 ring-[#58a6ff]/40 shadow-sm'
                  : 'bg-[#0d1117] border-[#30363d] hover:bg-[#161b22] hover:border-[#848d97]'
              }`}
            >
              <div>
                <div className="flex items-center justify-between gap-1 mb-1.5">
                  <span className="text-[10px] font-mono text-[#848d97] px-1.5 py-0.2 rounded bg-[#161b22] border border-[#30363d]">
                    {sha}
                  </span>
                  <span className={`text-[10px] font-mono px-1.5 py-0.2 rounded border font-semibold shrink-0 ${preset.badgeColor}`}>
                    {preset.tag}
                  </span>
                </div>

                <div className="text-xs font-semibold text-[#e6edf3] group-hover:text-[#58a6ff] transition mb-1 line-clamp-1">
                  {preset.name}
                </div>

                <p className="text-[11px] text-[#848d97] leading-snug line-clamp-2">
                  {preset.description}
                </p>
              </div>

              <div className="mt-2.5 pt-2 border-t border-[#30363d]/70 flex items-center justify-between text-[10px] text-[#848d97] font-mono">
                <span>Scenario {sha}</span>
                <span className="text-[#58a6ff] opacity-0 group-hover:opacity-100 transition flex items-center space-x-1">
                  <span>Run</span>
                  <ArrowRight className="w-2.5 h-2.5" />
                </span>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
};
