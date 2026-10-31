import React, { useState, useEffect } from "react";
import { BarChart3, RefreshCw, Users, HelpCircle, CheckCircle2, TrendingUp, Sparkles, Compass } from "lucide-react";

export default function MetricsView() {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchMetrics = () => {
    setLoading(true);
    fetch("/api/metrics")
      .then((res) => res.json())
      .then((data) => {
        setMetrics(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  };

  useEffect(() => {
    fetchMetrics();
  }, []);

  return (
    <div className="max-w-md mx-auto px-4 pt-3 pb-24 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <span className="text-[11px] font-semibold text-[#F4B8DC] uppercase tracking-wider block">
            Melooha Challenge Instrument
          </span>
          <h2 className="font-serif text-xl font-bold text-white flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-[#E5A93C]" />
            Conversion & Retention Metrics
          </h2>
        </div>
        <button
          onClick={fetchMetrics}
          className="p-2 rounded-xl bg-[#1A1230] border border-[#352554] text-[#A299BC] hover:text-white transition-colors"
          title="Refresh metrics"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin text-[#B21E68]" : ""}`} />
        </button>
      </div>

      {/* Primary KPI Card: Second-Question Retention Rate */}
      <div className="glass-panel p-6 relative overflow-hidden border-[#B21E68]/60">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold text-[#A299BC] uppercase tracking-wider">
            Primary Challenge Metric
          </span>
          <span className="text-xs px-2.5 py-0.5 rounded-full bg-[#B21E68]/20 text-[#F4B8DC] border border-[#B21E68]/40 font-medium">
            2nd Question Retention
          </span>
        </div>

        <div className="flex items-center gap-4 my-3">
          <div className="w-20 h-20 rounded-full border-4 border-[#B21E68] flex flex-col items-center justify-center text-white font-bold text-xl shadow-xl shadow-[#B21E68]/40 shrink-0">
            <span>{metrics ? `${metrics.second_question_retention_rate_pct}%` : "0%"}</span>
          </div>
          <div>
            <h3 className="font-serif text-lg font-bold text-white">
              Free Users Asking a 2nd Question
            </h3>
            <p className="text-xs text-[#A299BC] mt-1 leading-relaxed">
              Measures whether grounded evidence chips and trustworthy readings motivate users to explore further.
            </p>
          </div>
        </div>
      </div>

      {/* Metric Breakdown Grid */}
      <div className="grid grid-cols-2 gap-2.5 text-xs">
        <div className="glass-panel p-3.5 space-y-1">
          <span className="text-[#8E82AA] flex items-center gap-1">
            <Users className="w-3.5 h-3.5 text-cyan-400" />
            Total Users
          </span>
          <span className="text-xl font-bold text-white block">
            {metrics?.total_users ?? 0}
          </span>
        </div>

        <div className="glass-panel p-3.5 space-y-1">
          <span className="text-[#8E82AA] flex items-center gap-1">
            <HelpCircle className="w-3.5 h-3.5 text-[#E5A93C]" />
            Questions Asked
          </span>
          <span className="text-xl font-bold text-white block">
            {metrics?.total_questions_asked ?? 0}
          </span>
        </div>

        <div className="glass-panel p-3.5 space-y-1">
          <span className="text-[#8E82AA] flex items-center gap-1">
            <TrendingUp className="w-3.5 h-3.5 text-emerald-400" />
            Asked 2nd Question
          </span>
          <span className="text-xl font-bold text-white block">
            {metrics?.users_asked_second_question ?? 0}
          </span>
        </div>

        <div className="glass-panel p-3.5 space-y-1">
          <span className="text-[#8E82AA] flex items-center gap-1">
            <Compass className="w-3.5 h-3.5 text-[#F4B8DC]" />
            Evidence Opened
          </span>
          <span className="text-xl font-bold text-white block">
            {metrics?.evidence_opened_count ?? 0}
          </span>
        </div>
      </div>

      {/* Idea Documentation Note */}
      <div className="glass-panel p-4 text-xs text-[#A299BC] space-y-2">
        <div className="flex items-center gap-2 text-white font-semibold">
          <Sparkles className="w-4 h-4 text-[#E5A93C]" />
          <span>Product Hypothesis Behind This Metric</span>
        </div>
        <p className="leading-relaxed">
          As detailed in <code>docs/idea.md</code>, traditional AI astrology suffers from a "hallucination trust deficit". By anchoring readings to verifiable <strong>Evidence Chips</strong>, users experience the reading as an astronomical reflection rather than an arbitrary fortune, increasing second-question retention.
        </p>
      </div>
    </div>
  );
}
