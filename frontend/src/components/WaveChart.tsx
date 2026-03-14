import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface WaveChartProps {
  data: Array<{ wave: number; count: number; tier?: string }>;
}

export const WaveChart: React.FC<WaveChartProps> = ({ data }) => {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="wave" label={{ value: 'Wave', position: 'insideBottom', offset: -5 }} />
        <YAxis label={{ value: 'Count', angle: -90, position: 'insideLeft' }} />
        <Tooltip />
        <Legend />
        <Bar dataKey="count" fill="#02C39A" name="Companies" />
      </BarChart>
    </ResponsiveContainer>
  );
};

export default WaveChart;
