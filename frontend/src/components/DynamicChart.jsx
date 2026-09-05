import React from 'react';
import { ResponsiveContainer, LineChart, Line, BarChart, Bar, XAxis, YAxis, Tooltip, Legend, CartesianGrid, PieChart, Pie, Cell } from 'recharts';

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#14b8a6', '#6366f1'];

export default function DynamicChart({ chartType, chartData }) {
  if (!chartData || chartData.length === 0) {
    return <div className="text-gray-400 text-sm italic py-4 text-center">No visualization data returned for query.</div>;
  }

  const sampleKey = Object.keys(chartData[0] || {});
  const xKey = sampleKey.includes('name') ? 'name' : (sampleKey.includes('month') ? 'month' : sampleKey[0]);
  const valueKeys = sampleKey.filter(k => k !== xKey && k !== 'type');

  if (chartType === 'line') {
    return (
      <div className="h-72 w-full mt-4">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis dataKey={xKey} stroke="#64748b" fontSize={12} />
            <YAxis stroke="#64748b" fontSize={12} />
            <Tooltip contentStyle={{ backgroundColor: '#fff', borderRadius: '8px', border: '1px solid #e2e8f0' }} />
            <Legend />
            {valueKeys.map((vk, idx) => (
              <Line
                key={vk}
                type="monotone"
                dataKey={vk}
                stroke={COLORS[idx % COLORS.length]}
                strokeWidth={2.5}
                dot={{ r: 4 }}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    );
  }

  if (chartType === 'pie') {
    return (
      <div className="h-72 w-full mt-4 flex justify-center">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={chartData}
              dataKey={valueKeys[0] || 'value'}
              nameKey={xKey}
              cx="50%"
              cy="50%"
              outerRadius={80}
              label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
            >
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip contentStyle={{ backgroundColor: '#fff', borderRadius: '8px', border: '1px solid #e2e8f0' }} />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </div>
    );
  }

  // Default to Bar chart
  return (
    <div className="h-72 w-full mt-4">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
          <XAxis dataKey={xKey} stroke="#64748b" fontSize={12} />
          <YAxis stroke="#64748b" fontSize={12} />
          <Tooltip contentStyle={{ backgroundColor: '#fff', borderRadius: '8px', border: '1px solid #e2e8f0' }} />
          <Legend />
          {valueKeys.map((vk, idx) => (
            <Bar
              key={vk}
              dataKey={vk}
              fill={COLORS[idx % COLORS.length]}
              radius={[4, 4, 0, 0]}
            />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
