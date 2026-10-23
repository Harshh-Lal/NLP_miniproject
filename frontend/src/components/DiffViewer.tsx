import { useState, useMemo } from 'react';
import { Copy, Check, FileCode, ChevronDown, ChevronRight } from 'lucide-react';

interface DiffViewerProps {
  diffText: string;
}

interface ParsedFile {
  name: string;
  lines: string[];
  added: number;
  removed: number;
}

export const DiffViewer = ({ diffText }: DiffViewerProps) => {
  const [copied, setCopied] = useState(false);
  const [activeFileIndex, setActiveFileIndex] = useState<number>(0);
  const [isExpanded, setIsExpanded] = useState<boolean>(true);

  // Parse diff into separate files if present
  const files: ParsedFile[] = useMemo(() => {
    if (!diffText.trim()) return [];

    const fileBlocks = diffText.split(/(?=diff --git)/g).filter(Boolean);
    if (fileBlocks.length === 0) {
      // Fallback: whole diff as single file
      const rawLines = diffText.split('\n');
      const added = rawLines.filter((l) => l.startsWith('+') && !l.startsWith('+++')).length;
      const removed = rawLines.filter((l) => l.startsWith('-') && !l.startsWith('---')).length;
      return [{ name: 'unified.diff', lines: rawLines, added, removed }];
    }

    return fileBlocks.map((block) => {
      const lines = block.split('\n');
      const headerLine = lines.find((l) => l.startsWith('diff --git'));
      let fileName = 'unknown.py';
      if (headerLine) {
        const parts = headerLine.split(' ');
        if (parts.length >= 4) {
          fileName = parts[3].replace(/^b\//, '');
        }
      }
      const added = lines.filter((l) => l.startsWith('+') && !l.startsWith('+++')).length;
      const removed = lines.filter((l) => l.startsWith('-') && !l.startsWith('---')).length;

      return {
        name: fileName,
        lines,
        added,
        removed,
      };
    });
  }, [diffText]);

  const copyToClipboard = () => {
    navigator.clipboard.writeText(diffText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (!diffText.trim()) {
    return (
      <div className="p-6 text-center text-xs text-[#848d97] italic bg-[#0d1117] rounded-md border border-[#30363d]">
        No git diff provided. Paste a unified diff or choose a test scenario.
      </div>
    );
  }

  const currentFile = files[activeFileIndex] || files[0] || { name: 'unified.diff', lines: diffText.split('\n'), added: 0, removed: 0 };

  return (
    <div className="rounded-md border border-[#30363d] bg-[#0d1117] overflow-hidden shadow-sm">
      {/* GitHub Box Header & File Tabs */}
      <div className="bg-[#161b22] border-b border-[#30363d] px-3 py-2 flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-[#848d97] hover:text-[#e6edf3] transition p-1 rounded hover:bg-[#21262d] cursor-pointer"
            title={isExpanded ? 'Collapse Diff' : 'Expand Diff'}
          >
            {isExpanded ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
          </button>

          <span className="text-xs font-semibold text-[#e6edf3] flex items-center space-x-1.5">
            <FileCode className="w-3.5 h-3.5 text-[#848d97]" />
            <span>Files changed</span>
            <span className="text-[10px] font-mono px-1.5 py-0.2 rounded-full bg-[#30363d] text-[#848d97]">
              {files.length}
            </span>
          </span>
        </div>

        {/* File Tabs */}
        {files.length > 1 && (
          <div className="flex items-center space-x-1 bg-[#0d1117] p-0.5 rounded-md border border-[#30363d] overflow-x-auto max-w-full">
            {files.map((file, idx) => (
              <button
                key={idx}
                onClick={() => setActiveFileIndex(idx)}
                className={`px-2 py-0.5 rounded text-[11px] font-mono transition flex items-center space-x-1.5 cursor-pointer whitespace-nowrap ${
                  activeFileIndex === idx
                    ? 'bg-[#21262d] text-[#e6edf3] font-semibold border border-[#30363d]'
                    : 'text-[#848d97] hover:text-[#e6edf3] hover:bg-[#161b22]'
                }`}
              >
                <span>{file.name}</span>
                <span className="text-[10px] text-[#3fb950] font-sans">+{file.added}</span>
                <span className="text-[10px] text-[#f85149] font-sans">-{file.removed}</span>
              </button>
            ))}
          </div>
        )}

        {/* Copy Button */}
        <button
          onClick={copyToClipboard}
          className="text-xs px-2.5 py-1 rounded-md bg-[#21262d] hover:bg-[#30363d] text-[#c9d1d9] border border-[#30363d] flex items-center space-x-1.5 transition cursor-pointer"
        >
          {copied ? (
            <>
              <Check className="w-3 h-3 text-[#3fb950]" />
              <span className="text-[#3fb950] text-[11px]">Copied</span>
            </>
          ) : (
            <>
              <Copy className="w-3 h-3 text-[#848d97]" />
              <span className="text-[11px]">Copy Raw Diff</span>
            </>
          )}
        </button>
      </div>

      {/* GitHub-Styled Unified Code Viewer Body */}
      {isExpanded && (
        <div className="font-mono text-xs overflow-x-auto max-h-[380px] bg-[#0d1117] select-text">
          {currentFile.lines.map((line, idx) => {
            let rowBg = 'hover:bg-[#161b22]/60 text-[#c9d1d9]';
            let gutterBg = 'text-[#6e7681]';
            let marker = ' ';

            if (line.startsWith('+++') || line.startsWith('---')) {
              rowBg = 'text-[#848d97] font-semibold bg-[#161b22] border-b border-[#30363d]/50';
              gutterBg = 'text-[#6e7681] bg-[#161b22]';
            } else if (line.startsWith('+')) {
              rowBg = 'bg-[#2ea043]/15 text-[#e6edf3]';
              gutterBg = 'bg-[#2ea043]/20 text-[#3fb950]';
              marker = '+';
            } else if (line.startsWith('-')) {
              rowBg = 'bg-[#da3633]/15 text-[#e6edf3]';
              gutterBg = 'bg-[#da3633]/20 text-[#f85149]';
              marker = '-';
            } else if (line.startsWith('@@')) {
              rowBg = 'bg-[#388bfd]/10 text-[#79c0ff] border-y border-[#388bfd]/20 my-0.5';
              gutterBg = 'bg-[#388bfd]/15 text-[#79c0ff]';
            } else if (line.startsWith('diff --git')) {
              rowBg = 'text-[#e6edf3] font-semibold bg-[#161b22] border-t border-[#30363d] mt-1';
              gutterBg = 'text-[#848d97] bg-[#161b22]';
            }

            return (
              <div key={idx} className={`flex items-stretch whitespace-pre text-[12px] leading-5 ${rowBg}`}>
                <span className={`w-10 select-none text-right pr-2 shrink-0 border-r border-[#30363d]/40 font-mono text-[11px] py-0.5 ${gutterBg}`}>
                  {idx + 1}
                </span>
                <span className="w-5 select-none font-bold text-center shrink-0 py-0.5">
                  {marker !== ' ' ? marker : ''}
                </span>
                <span className="flex-1 py-0.5 pr-2 break-all">{line}</span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
