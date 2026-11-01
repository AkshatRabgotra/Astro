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
    <div className="max-w-md mx-auto px-4 pt-3 pb-28 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <span className="text-[10px] font-bold text-[#F4B8DC] uppercase tracking-wider block">
            Melooha Challenge Instrument
          </span>
          <h2 className="font-serif text-lg sm:text-xl font-bold text-white flex items-center gap-2">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-[#931B58] to-[#B21E68] text-white flex items-center justify-center shadow-md">
              <BarChart3 className="w-4 h-4 text-[#FDE68A]" />
            </div>
            <span>Conversion & Retention</span>
          </h2>
        </div>
        <button
          onClick={fetchMetrics}
          className="p-2 rounded-xl astro-badge text-[#A299BC] hover:text-white transition-colors"
          title="Refresh metrics"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin text-[#B21E68]" : ""}`} />
        </button>
      </div>

      {/* Primary KPI Card: Second-Question Retention Rate */}
      <div className="crystal-card p-6 relative overflow-hidden border-[#B21E68]/60 space-y-3">
        {/* Subtle Watermark */}
        <div className="absolute -top-4 -right-4 text-4xl text-white/[0.03] select-none pointer-events-none font-serif">
          ✦ ♃ ☉
        </div>

        <div className="flex items-center justify-between">
          <span className="text-[11px] font-bold text-[#A299BC] uppercase tracking-wider">
            Primary Challenge Metric
          </span>
          <span className="astro-badge px-2.5 py-0.5 rounded-full text-xs text-[#F4B8DC] font-bold">
            2nd Question Retention
          </span>
        </div>

        <div className="flex items-center gap-4 my-2">
          <div className="w-20 h-20 rounded-full border-4 border-[#B21E68] flex flex-col items-center justify-center text-white font-bold text-xl shadow-xl shadow-[#B21E68]/40 cosmic-glow shrink-0 bg-[#160E28]">
            <span className="shimmer-text-plum">{metrics ? `${metrics.second_question_retention_rate_pct}%` : "0%"}</span>
          </div>
          <div>
            <h3 className="font-serif text-base sm:text-lg font-bold text-white">
              Free Users Asking a 2nd Question
            </h3>
            <p className="text-xs text-[#A299BC] mt-0.5 leading-relaxed">
              Measures whether grounded evidence chips and trustworthy readings motivate users to explore further.
            </p>
          </div>
        </div>
      </div>

      {/* Metric Breakdown Grid */}
      <div className="grid grid-cols-2 gap-2.5 text-xs">
        <div className="crystal-card p-3.5 space-y-1">
          <span className="text-[#8E82AA] flex items-center gap-1.5 font-medium">
            <Users className="w-3.5 h-3.5 text-cyan-400" />
            Total Users
          </span>
          <span className="text-xl font-bold text-white block">
            {metrics?.total_users ?? 0}
          </span>
        </div>

        <div className="crystal-card p-3.5 space-y-1">
          <span className="text-[#8E82AA] flex items-center gap-1.5 font-medium">
            <HelpCircle className="w-3.5 h-3.5 text-[#E5A93C]" />
            Questions Asked
          </span>
          <span className="text-xl font-bold text-white block">
            {metrics?.total_questions_asked ?? 0}
          </span>
        </div>

        <div className="crystal-card p-3.5 space-y-1">
          <span className="text-[#8E82AA] flex items-center gap-1.5 font-medium">
            <TrendingUp className="w-3.5 h-3.5 text-emerald-400" />
            Asked 2nd Question
          </span>
          <span className="text-xl font-bold text-white block">
            {metrics?.users_asked_second_question ?? 0}
          </span>
        </div>

        <div className="crystal-card p-3.5 space-y-1">
          <span className="text-[#8E82AA] flex items-center gap-1.5 font-medium">
            <Compass className="w-3.5 h-3.5 text-[#F4B8DC]" />
            Evidence Opened
          </span>
          <span className="text-xl font-bold text-white block">
            {metrics?.evidence_opened_count ?? 0}
          </span>
        </div>
      </div>

      {/* Idea Documentation Note */}
      <div className="crystal-card p-4 text-xs text-[#A299BC] space-y-2">
        <div className="flex items-center gap-2 text-white font-bold">
          <Sparkles className="w-4 h-4 text-[#E5A93C]" />
          <span>Product Hypothesis Behind This Metric</span>
        </div>
        <p className="leading-relaxed text-[#C5B9DF]">
          As detailed in <code>docs/idea.md</code>, traditional AI astrology suffers from a "hallucination trust deficit". By anchoring readings to verifiable <strong>Evidence Chips</strong>, users experience the reading as an astronomical reflection rather than an arbitrary fortune, increasing second-question retention.
        </p>
      </div>
    </div>
  );
}
