import type { FC } from 'react';
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Tooltip,
} from 'recharts';

interface ScoreRadarChartProps {
  scores: {
    imperative: number | null;
    coverage: number | null;
    risk: number | null;
    typeConsistency: number | null;
  };
}

const CustomTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="bg-[#161b22] border border-[#30363d] p-2.5 rounded-md shadow-lg text-xs">
        <p className="font-semibold text-[#e6edf3] mb-0.5">{data.subject}</p>
        <p className="text-[#58a6ff] font-mono font-semibold">{data.value}% Consistency</p>
      </div>
    );
  }
  return null;
};

export const ScoreRadarChart: FC<ScoreRadarChartProps> = ({ scores }) => {
  const axes = [
    { subject: 'Imperative Mood', val: scores.imperative },
    { subject: 'Symbol Coverage', val: scores.coverage },
    { subject: 'Arch Safety', val: scores.risk },
    { subject: 'Type Match', val: scores.typeConsistency },
  ];

  // If score is null, omit axis or display 0 with an inactive flag
  const data = axes.map((a) => ({
    subject: a.subject,
    value: a.val !== null && a.val !== undefined ? Math.round((a.val as number) * 100) : 0,
    isActive: a.val !== null && a.val !== undefined,
    fullMark: 100,
  }));

  return (
    <div className="w-full h-64 flex items-center justify-center relative">
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart cx="50%" cy="50%" outerRadius="70%" data={data}>
          <PolarGrid stroke="#30363d" />
          <PolarAngleAxis
            dataKey="subject"
            stroke="#848d97"
            tick={{ fill: '#848d97', fontSize: 11, fontWeight: 500 }}
          />
          <PolarRadiusAxis angle={30} domain={[0, 100]} stroke="#30363d" tick={false} />
          <Radar
            name="Consistency"
            dataKey="value"
            stroke="#58a6ff"
            strokeWidth={1.5}
            fill="#1f6feb"
            fillOpacity={0.25}
          />
          <Tooltip content={<CustomTooltip />} />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
};
