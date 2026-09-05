import React, { useState } from 'react';
import { Cpu, Filter, Layers, Database, Code, ChevronDown, ChevronUp } from 'lucide-react';

export default function ExplainabilityPanel({ explainability, dataTable }) {
  const [showTable, setShowTable] = useState(false);

  if (!explainability) return null;

  const filters = explainability.applied_filters || {};
  const filterEntries = Object.entries(filters);

  return (
    <div className="mt-6 bg-slate-900 text-slate-100 p-5 rounded-xl border border-slate-800 shadow-md">
      <div className="flex items-center gap-2 mb-4 border-b border-slate-800 pb-3">
        <Cpu className="w-5 h-5 text-sky-400" />
        <h4 className="text-base font-bold tracking-wide text-sky-400">Explainability & Computation Audit</h4>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
        {/* Applied Filters */}
        <div className="bg-slate-800/80 p-3 rounded-lg border border-slate-700/60">
          <div className="flex items-center gap-1.5 font-semibold text-slate-300 mb-2">
            <Filter className="w-4 h-4 text-emerald-400" />
            <span>Applied Filters</span>
          </div>
          {filterEntries.length > 0 ? (
            <ul className="space-y-1 text-slate-400 font-mono">
              {filterEntries.map(([k, v]) => (
                <li key={k} className="truncate">
                  <span className="text-slate-200">{k}:</span> {String(v)}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-slate-500 italic">None (Full Dataset)</p>
          )}
        </div>

        {/* Metrics & Dimensions */}
        <div className="bg-slate-800/80 p-3 rounded-lg border border-slate-700/60">
          <div className="flex items-center gap-1.5 font-semibold text-slate-300 mb-2">
            <Layers className="w-4 h-4 text-purple-400" />
            <span>Metrics & Dimensions</span>
          </div>
          <div className="flex flex-wrap gap-1">
            {(explainability.metrics_and_dimensions || []).map((md, idx) => (
              <span key={idx} className="bg-slate-700 text-purple-300 px-2 py-0.5 rounded text-[11px] font-mono">
                {md}
              </span>
            ))}
          </div>
        </div>

        {/* Query Plan / Methodology */}
        <div className="bg-slate-800/80 p-3 rounded-lg border border-slate-700/60">
          <div className="flex items-center gap-1.5 font-semibold text-slate-300 mb-2">
            <Code className="w-4 h-4 text-amber-400" />
            <span>Computation Plan</span>
          </div>
          <p className="text-slate-300 leading-relaxed">
            {explainability.query_plan || explainability.methodology || "No execution plan specified."}
          </p>
          {explainability.sql_executed && (
            <div className="mt-2 text-[10px] bg-slate-950 p-2 rounded text-amber-200/90 font-mono overflow-x-auto">
              {explainability.sql_executed}
            </div>
          )}
        </div>
      </div>

      {/* Raw Data Toggle & Table */}
      {dataTable && dataTable.length > 0 && (
        <div className="mt-4 pt-3 border-t border-slate-800">
          <button
            onClick={() => setShowTable(!showTable)}
            className="flex items-center justify-between w-full text-xs font-semibold text-slate-400 hover:text-slate-200 transition-colors py-1"
          >
            <span className="flex items-center gap-1.5">
              <Database className="w-4 h-4 text-sky-400" />
              Underlying Raw Data Table ({dataTable.length} rows)
            </span>
            {showTable ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>

          {showTable && (
            <div className="mt-3 overflow-x-auto rounded-lg border border-slate-800 bg-slate-950 max-h-60 overflow-y-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-900 text-slate-400 sticky top-0 font-mono">
                  <tr>
                    {Object.keys(dataTable[0]).map((col) => (
                      <th key={col} className="px-3 py-2 border-b border-slate-800">{col}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/50 font-mono text-[11px]">
                  {dataTable.map((row, idx) => (
                    <tr key={idx} className="hover:bg-slate-900/50">
                      {Object.values(row).map((val, cidx) => (
                        <td key={cidx} className="px-3 py-1.5 whitespace-nowrap">
                          {val !== null && val !== undefined ? String(val) : '-'}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
