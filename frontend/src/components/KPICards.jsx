import React from 'react';
import { Package, Truck, AlertTriangle, CheckCircle2, Clock, DollarSign } from 'lucide-react';

export default function KPICards({ kpis }) {
  if (!kpis) return null;

  const cards = [
    {
      title: "Total Orders",
      value: kpis.total_orders?.toLocaleString() || "0",
      icon: Package,
      color: "text-blue-600",
      bg: "bg-blue-50",
      border: "border-blue-200"
    },
    {
      title: "Delivered Orders",
      value: kpis.delivered_orders?.toLocaleString() || "0",
      icon: CheckCircle2,
      color: "text-emerald-600",
      bg: "bg-emerald-50",
      border: "border-emerald-200"
    },
    {
      title: "Delayed Orders",
      value: kpis.delayed_orders?.toLocaleString() || "0",
      icon: AlertTriangle,
      color: "text-amber-600",
      bg: "bg-amber-50",
      border: "border-amber-200"
    },
    {
      title: "On-Time Rate",
      value: `${kpis.on_time_delivery_rate_pct || 0}%`,
      icon: Truck,
      color: "text-indigo-600",
      bg: "bg-indigo-50",
      border: "border-indigo-200"
    },
    {
      title: "Avg Delivery Time",
      value: `${kpis.avg_delivery_time_days || 0} days`,
      icon: Clock,
      color: "text-purple-600",
      bg: "bg-purple-50",
      border: "border-purple-200"
    },
    {
      title: "Total Order Value",
      value: `$${(kpis.total_revenue_usd || 0).toLocaleString()}`,
      icon: DollarSign,
      color: "text-teal-600",
      bg: "bg-teal-50",
      border: "border-teal-200"
    }
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
      {cards.map((card, idx) => {
        const Icon = card.icon;
        return (
          <div key={idx} className={`bg-white p-4 rounded-xl border ${card.border} shadow-xs transition-all hover:shadow-md`}>
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">{card.title}</span>
              <div className={`p-2 rounded-lg ${card.bg}`}>
                <Icon className={`w-5 h-5 ${card.color}`} />
              </div>
            </div>
            <div className="text-2xl font-bold text-gray-900">{card.value}</div>
          </div>
        );
      })}
    </div>
  );
}
