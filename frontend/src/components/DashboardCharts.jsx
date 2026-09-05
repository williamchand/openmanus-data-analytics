import React from 'react';
import { ResponsiveContainer, LineChart, Line, BarChart, Bar, XAxis, YAxis, Tooltip, Legend, CartesianGrid, PieChart, Pie, Cell } from 'recharts';

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#14b8a6'];

export default function DashboardCharts({ orderVolume, carrierData, performanceData }) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
      {/* Order Volume Over Time */}
      <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-xs">
        <h3 className="text-base font-bold text-gray-800 mb-4">Order Volume & Performance Over Time</h3>
        <div className="h-72">
          {orderVolume && orderVolume.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={orderVolume}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="month" stroke="#64748b" fontSize={12} />
                <YAxis stroke="#64748b" fontSize={12} />
                <Tooltip contentStyle={{ backgroundColor: '#fff', borderRadius: '8px', border: '1px solid #e2e8f0' }} />
                <Legend />
                <Line type="monotone" dataKey="total_orders" stroke="#3b82f6" strokeWidth={2.5} name="Total Orders" />
                <Line type="monotone" dataKey="delivered" stroke="#10b981" strokeWidth={2} name="Delivered" />
                <Line type="monotone" dataKey="delayed" stroke="#f59e0b" strokeWidth={2} name="Delayed" />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-full flex items-center justify-center text-gray-400">Loading chart data...</div>
          )}
        </div>
      </div>

      {/* Carrier Delay Rate Breakdown */}
      <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-xs">
        <h3 className="text-base font-bold text-gray-800 mb-4">Carrier Delay Rate (%) & Volume</h3>
        <div className="h-72">
          {carrierData && carrierData.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={carrierData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="carrier" stroke="#64748b" fontSize={12} />
                <YAxis stroke="#64748b" fontSize={12} />
                <Tooltip contentStyle={{ backgroundColor: '#fff', borderRadius: '8px', border: '1px solid #e2e8f0' }} />
                <Legend />
                <Bar dataKey="total_orders" fill="#93c5fd" name="Total Orders" radius={[4, 4, 0, 0]} />
                <Bar dataKey="delayed_orders" fill="#f87171" name="Delayed Orders" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-full flex items-center justify-center text-gray-400">Loading carrier data...</div>
          )}
        </div>
      </div>
    </div>
  );
}
