import React from 'react';
import { RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, Legend, Tooltip, ResponsiveContainer } from 'recharts';

interface ScoreRadarProps {
  scores: Record<string, number>;
}

export const ScoreRadar: React.FC<ScoreRadarProps> = ({ scores }) => {
  const data = Object.entries(scores).map(([key, value]) => ({
    name: key
      .split('_')
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' '),
    score: typeof value === 'number' ? value : 0,
  }));

  return (
    <ResponsiveContainer width="100%" height={400}>
      <RadarChart data={data}>
        <PolarGrid stroke="#e5e7eb" />
        <PolarAngleAxis dataKey="name" tick={{ fontSize: 12 }} />
        <PolarRadiusAxis angle={90} domain={[0, 5]} />
        <Radar name="Score" dataKey="score" stroke="#02C39A" fill="#02C39A" fillOpacity={0.6} />
        <Tooltip formatter={(value) => Number(value).toFixed(2)} />
        <Legend />
      </RadarChart>
    </ResponsiveContainer>
  );
};

export default ScoreRadar;
