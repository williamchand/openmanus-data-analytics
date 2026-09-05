import React, { useState, useEffect } from 'react';
import { Sparkles, RefreshCw, Send, HelpCircle, BarChart3, Bot, Search } from 'lucide-react';
import KPICards from './components/KPICards';
import DashboardCharts from './components/DashboardCharts';
import DynamicChart from './components/DynamicChart';
import ExplainabilityPanel from './components/ExplainabilityPanel';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

const SAMPLE_QUESTIONS = [
  "Which carrier has the highest delay rate?",
  "Show delayed orders by week for the last 3 months",
  "Predict demand for SKU PAPER-0197 for the next 4 months",
  "Show order summary by product category",
  "How many orders were delivered late or canceled?"
];

export default function App() {
  const [kpis, setKpis] = useState(null);
  const [orderVolume, setOrderVolume] = useState([]);
  const [carrierData, setCarrierData] = useState([]);
  const [loadingDashboard, setLoadingDashboard] = useState(true);

  // AI Interface states
  const [question, setQuestion] = useState('');
  const [aiLoading, setAiLoading] = useState(false);
  const [aiResponse, setAiResponse] = useState(null);
  const [aiError, setAiError] = useState(null);

  const fetchDashboardData = async () => {
    setLoadingDashboard(true);
    try {
      const [kpiRes, volRes, carrierRes] = await Promise.all([
        fetch(`${API_BASE_URL}/api/kpis`),
        fetch(`${API_BASE_URL}/api/charts/order-volume`),
        fetch(`${API_BASE_URL}/api/charts/carrier-breakdown`)
      ]);

      const kpiData = await kpiRes.json();
      const volData = await volRes.json();
      const carrierData = await carrierRes.json();

      setKpis(kpiData);
      setOrderVolume(volData.chart_data || []);
      setCarrierData(carrierData.chart_data || []);
    } catch (err) {
      console.error('Error fetching dashboard data:', err);
    } finally {
      setLoadingDashboard(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const handleAskAI = async (qToAsk) => {
    const q = qToAsk || question;
    if (!q || !q.trim()) return;

    setQuestion(q);
    setAiLoading(true);
    setAiError(null);

    try {
      const res = await fetch(`${API_BASE_URL}/api/ask-ai`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: q })
      });

      if (!res.ok) {
        throw new Error(`Server responded with status ${res.status}`);
      }

      const data = await res.json();
      setAiResponse(data);
    } catch (err) {
      setAiError(err.message || 'Failed to process natural language query.');
    } finally {
      setAiLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 pb-12">
      {/* Navbar */}
      <header className="bg-slate-900 text-white border-b border-slate-800 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="bg-blue-600 p-2 rounded-lg">
              <BarChart3 className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight">AI Logistics Intelligence</h1>
              <p className="text-xs text-slate-400">Descriptive, Diagnostic & Predictive Logistics Analytics Platform</p>
            </div>
          </div>
          <button
            onClick={fetchDashboardData}
            className="flex items-center gap-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs px-3 py-2 rounded-lg border border-slate-700 transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loadingDashboard ? 'animate-spin' : ''}`} />
            <span>Refresh Data</span>
          </button>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-6 space-y-8">
        {/* Section 1: Descriptive Analytics Dashboard */}
        <section>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-blue-600" />
              Operational Performance Dashboard
            </h2>
            <span className="text-xs text-slate-500 font-medium">Data source: Logistics DB (400 synced records)</span>
          </div>

          <KPICards kpis={kpis} />
          <DashboardCharts orderVolume={orderVolume} carrierData={carrierData} />
        </section>

        {/* Section 2: AI-Powered Natural Language Interface */}
        <section className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
          <div className="flex items-center gap-2 mb-4">
            <div className="bg-purple-100 p-2 rounded-lg">
              <Bot className="w-5 h-5 text-purple-600" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-900">Natural Language & Predictive Intelligence Agent</h2>
              <p className="text-xs text-slate-500">Ask operational questions, analyze delay drivers, or request time-series inventory predictions.</p>
            </div>
          </div>

          {/* Question Input Box */}
          <form onSubmit={(e) => { e.preventDefault(); handleAskAI(); }} className="flex gap-2">
            <div className="relative flex-1">
              <Search className="w-5 h-5 text-slate-400 absolute left-3.5 top-3.5" />
              <input
                type="text"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="Ask any logistics question (e.g. 'Which carrier has highest delay rate?', 'Predict demand for SKU PAPER-0197')..."
                className="w-full pl-11 pr-4 py-3 bg-slate-50 border border-slate-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all"
              />
            </div>
            <button
              type="submit"
              disabled={aiLoading || !question.trim()}
              className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-medium px-5 py-3 rounded-xl flex items-center gap-2 text-sm transition-all shadow-xs"
            >
              {aiLoading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
              <span>Query AI</span>
            </button>
          </form>

          {/* Sample Question Chips */}
          <div className="mt-3 flex flex-wrap items-center gap-2">
            <span className="text-xs font-semibold text-slate-400 flex items-center gap-1">
              <HelpCircle className="w-3.5 h-3.5" /> Examples:
            </span>
            {SAMPLE_QUESTIONS.map((sq, idx) => (
              <button
                key={idx}
                onClick={() => handleAskAI(sq)}
                className="text-xs bg-slate-100 hover:bg-slate-200 text-slate-700 px-2.5 py-1 rounded-full border border-slate-200 transition-colors"
              >
                {sq}
              </button>
            ))}
          </div>

          {/* AI Response Display */}
          {aiError && (
            <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm">
              {aiError}
            </div>
          )}

          {aiResponse && (
            <div className="mt-6 p-5 bg-slate-50 border border-slate-200 rounded-xl space-y-4">
              {/* Direct Answer */}
              <div className="flex items-start gap-3 bg-white p-4 rounded-xl border border-slate-200 shadow-2xs">
                <Sparkles className="w-5 h-5 text-amber-500 shrink-0 mt-0.5" />
                <div>
                  <div className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">
                    AI Response ({aiResponse.tool_used})
                  </div>
                  <div className="text-slate-900 font-medium text-sm leading-relaxed">
                    {aiResponse.answer}
                  </div>
                </div>
              </div>

              {/* Dynamic Chart */}
              {aiResponse.chart_data && (
                <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs">
                  <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Dynamic Chart Visualization</h4>
                  <DynamicChart chartType={aiResponse.chart_type} chartData={aiResponse.chart_data} />
                </div>
              )}

              {/* Explainability Section */}
              <ExplainabilityPanel explainability={aiResponse.explainability} dataTable={aiResponse.data_table} />
            </div>
          )}
        </section>
      </main>

      <footer className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-12 text-center text-xs text-slate-400">
        AI-Powered Logistics Analytics & Dynamic Forecasting System • Built for Production
      </footer>
    </div>
  );
}
