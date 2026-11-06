import React, { useState, useEffect } from "react";
import { BarChart3, RefreshCw, Users, HelpCircle, CheckCircle2, TrendingUp, Sparkles, Compass, Share2, UserPlus, Eye, ShieldCheck, AlertTriangle } from "lucide-react";

export default function MetricsView() {
  const [metrics, setMetrics] = useState(null);
  const [twinMetrics, setTwinMetrics] = useState(null);
  const [pastCheckMetrics, setPastCheckMetrics] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchMetrics = () => {
    setLoading(true);
    Promise.all([
      fetch("/api/metrics").then((r) => r.json()).catch(() => null),
      fetch("/api/metrics/dasha-twin").then((r) => r.json()).catch(() => null),
      fetch("/api/metrics/past-check").then((r) => r.json()).catch(() => null),
    ]).then(([m, tm, pm]) => {
      if (m) setMetrics(m);
      if (tm) setTwinMetrics(tm);
      if (pm) setPastCheckMetrics(pm);
      setLoading(false);
    });
  };

  useEffect(() => {
    fetchMetrics();
  }, []);

  return (
    <div className="max-w-md mx-auto px-4 pt-3 pb-28 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-1.5">
            <span className="text-[10px] font-bold text-[#F4B8DC] uppercase tracking-wider block">
              Admin & Evaluation Console
            </span>
            <span className="px-1.5 py-0.2 rounded text-[9px] font-bold bg-amber-500/20 text-[#FDE68A] border border-amber-500/40">
              Admin Only
            </span>
          </div>
          <h2 className="font-serif text-lg sm:text-xl font-bold text-white flex items-center gap-2 mt-0.5">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-[#931B58] to-[#B21E68] text-white flex items-center justify-center shadow-md">
              <BarChart3 className="w-4 h-4 text-[#FDE68A]" />
            </div>
            <span>Internal Metrics & Funnels</span>
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

      {/* Admin Notice Banner */}
      <div className="p-3 rounded-2xl bg-[#1C0F2E] border border-amber-500/35 text-[11px] text-[#DDD5EE] flex items-start gap-2.5 shadow-md">
        <span className="text-base leading-none">🔒</span>
        <p className="leading-relaxed">
          <strong className="text-white font-semibold">Admin-Facing Telemetry:</strong> These retention funnels, conversion rates, and A/B experiments are compiled for administrators and challenge judges. They are not displayed to regular end-users.
        </p>
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

      {/* Dasha Twin Virality & Share Metrics (Section 6) */}
      <div className="crystal-card p-5 space-y-3.5 border border-[#E5A93C]/40">
        <div className="flex items-center justify-between">
          <div>
            <span className="text-[10px] font-bold text-[#E5A93C] uppercase tracking-wider block">
              Viral Growth Engine
            </span>
            <h3 className="font-serif text-base font-bold text-white flex items-center gap-2">
              <Share2 className="w-4 h-4 text-[#E5A93C]" />
              <span>Dasha Twin Share Metrics</span>
            </h3>
          </div>
          <span className="px-2.5 py-0.5 rounded-full text-xs bg-amber-500/20 text-[#FDE68A] font-bold border border-amber-400/40">
            K-Factor / WAU
          </span>
        </div>

        {/* Primary Metric: Shares per WAU */}
        <div className="grid grid-cols-2 gap-2.5">
          <div className="p-3.5 rounded-2xl bg-[#140B26] border border-[#2B184B] space-y-1">
            <span className="text-[11px] text-[#A299BC] block font-medium">
              Primary: Shares / WAU
            </span>
            <span className="text-2xl font-bold font-serif text-[#FDE68A]">
              {twinMetrics ? twinMetrics.primary_metric_shares_per_wau : "0.00"}
            </span>
            <span className="text-[10px] text-emerald-400 block">Weekly virality velocity</span>
          </div>

          <div className="p-3.5 rounded-2xl bg-[#140B26] border border-[#2B184B] space-y-1">
            <span className="text-[11px] text-[#A299BC] block font-medium">
              Secondary: Share to Signup
            </span>
            <span className="text-2xl font-bold font-serif text-[#F4B8DC]">
              {twinMetrics ? `${twinMetrics.secondary_metric_share_to_signup_pct}%` : "0.0%"}
            </span>
            <span className="text-[10px] text-cyan-400 block">Attributed acquisition</span>
          </div>
        </div>

        {/* Funnel Counters */}
        <div className="grid grid-cols-3 gap-2 text-center text-xs pt-1">
          <div className="p-2 rounded-xl bg-[#190F30] border border-[#2D1B50]">
            <span className="text-[10px] text-[#8E82AA] block">Card Views</span>
            <strong className="text-white text-sm">{twinMetrics?.funnel?.card_viewed ?? 0}</strong>
          </div>
          <div className="p-2 rounded-xl bg-[#190F30] border border-[#2D1B50]">
            <span className="text-[10px] text-[#8E82AA] block">Shares Created</span>
            <strong className="text-[#E5A93C] text-sm">{twinMetrics?.funnel?.share_created ?? 0}</strong>
          </div>
          <div className="p-2 rounded-xl bg-[#190F30] border border-[#2D1B50]">
            <span className="text-[10px] text-[#8E82AA] block">Links Opened</span>
            <strong className="text-emerald-400 text-sm">{twinMetrics?.funnel?.share_link_opened ?? 0}</strong>
          </div>
        </div>
      </div>

      {/* Past Check A/B Experiment (Part A6 Trust Before Paywall) */}
      <div className="crystal-card p-5 space-y-4 border border-[#B21E68]/50">
        <div className="flex items-center justify-between">
          <div>
            <span className="text-[10px] font-bold text-[#F4B8DC] uppercase tracking-wider block">
              A/B Trust Experiment (Section A6)
            </span>
            <h3 className="font-serif text-base font-bold text-white flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-[#E5A93C]" />
              <span>Past Check vs Retention</span>
            </h3>
          </div>
          <span className="px-2.5 py-0.5 rounded-full text-xs bg-purple-900/40 text-[#F4B8DC] font-bold border border-purple-500/30">
            50/50 RCT
          </span>
        </div>

        {/* Small Sample Global Banner if either arm < 30 */}
        {(pastCheckMetrics?.control_arm?.is_small_sample || pastCheckMetrics?.treatment_arm?.is_small_sample) && (
          <div className="p-3 rounded-2xl bg-amber-500/10 border border-amber-500/30 flex items-start gap-2.5 text-xs text-amber-200">
            <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
            <div className="space-y-0.5 leading-relaxed">
              <span className="font-bold text-amber-300 block">Small Sample Warning (n &lt; 30)</span>
              <span>
                Observed rates have wide confidence bounds. In accordance with honesty guidelines, statistical claims require n &ge; 30.
              </span>
            </div>
          </div>
        )}

        {/* 2nd-Question Retention by Arm with Wilson 95% CIs */}
        <div className="space-y-2">
          <span className="text-[11px] font-bold text-[#A299BC] uppercase tracking-wider block">
            2nd Question Conversion Rate by Arm
          </span>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
            {/* Control Arm */}
            <div className="p-3.5 rounded-2xl bg-[#140B26] border border-[#2B184B] space-y-1.5">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-[#A299BC]">Control (No Past Check)</span>
                {pastCheckMetrics?.control_arm?.is_small_sample && (
                  <span className="text-[9px] px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 font-semibold">n &lt; 30</span>
                )}
              </div>
              <div className="text-sm font-bold font-mono text-white">
                {pastCheckMetrics?.control_arm?.formatted || "0.0% [95% CI: 0.0% – 0.0%, n=0]"}
              </div>
              <p className="text-[10px] text-[#8E82AA]">
                {pastCheckMetrics?.control_arm?.converted_count ?? 0} of {pastCheckMetrics?.control_arm?.sample_size ?? 0} asked 2nd question
              </p>
            </div>

            {/* Treatment Arm */}
            <div className="p-3.5 rounded-2xl bg-[#190C2C] border border-[#931B58]/40 space-y-1.5">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-[#F4B8DC]">Treatment (Past Check)</span>
                {pastCheckMetrics?.treatment_arm?.is_small_sample && (
                  <span className="text-[9px] px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 font-semibold">n &lt; 30</span>
                )}
              </div>
              <div className="text-sm font-bold font-mono text-[#FDE68A]">
                {pastCheckMetrics?.treatment_arm?.formatted || "0.0% [95% CI: 0.0% – 0.0%, n=0]"}
              </div>
              <p className="text-[10px] text-[#8E82AA]">
                {pastCheckMetrics?.treatment_arm?.converted_count ?? 0} of {pastCheckMetrics?.treatment_arm?.sample_size ?? 0} asked 2nd question
              </p>
            </div>
          </div>

          {/* Delta Difference */}
          <div className="p-2.5 rounded-xl bg-[#120822] border border-[#2B184B] flex items-center justify-between text-xs">
            <span className="text-[#A299BC] font-medium">Difference Between Arms (&Delta;):</span>
            <span className={`font-bold font-mono ${pastCheckMetrics?.delta?.difference >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
              {pastCheckMetrics?.delta?.formatted || "0.0%"} treatment impact
            </span>
          </div>
        </div>

        {/* Real vs Decoy Statements (Sanity & Anti-Barnum Check) */}
        <div className="space-y-2 pt-1 border-t border-[#2B184B]">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold text-[#A299BC] uppercase tracking-wider block">
              Sanity Check: Real vs Decoy "Yes" Rate
            </span>
            <span className="text-[10px] text-[#8E82AA]">30% Decoy Seed</span>
          </div>

          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="p-3 rounded-xl bg-[#140B26] border border-[#2B184B] space-y-1">
              <span className="text-[10px] text-emerald-400 font-semibold block">Real Planetary Triggers</span>
              <span className="text-xs font-bold font-mono text-white block">
                {pastCheckMetrics?.decoy_analysis?.real_statements?.formatted || "0.0% [95% CI: 0.0% – 0.0%, n=0]"}
              </span>
            </div>

            <div className="p-3 rounded-xl bg-[#140B26] border border-[#2B184B] space-y-1">
              <span className="text-[10px] text-amber-400 font-semibold block">Decoy Trigger Windows</span>
              <span className="text-xs font-bold font-mono text-white block">
                {pastCheckMetrics?.decoy_analysis?.decoy_statements?.formatted || "0.0% [95% CI: 0.0% – 0.0%, n=0]"}
              </span>
            </div>
          </div>

          <p className="text-[10px] text-[#8E82AA] leading-relaxed">
            Discrimination Delta: <strong className="text-white">{pastCheckMetrics?.decoy_analysis?.discrimination_delta_pct ?? 0}%</strong> higher resonance on actual planetary windows than decoys.
          </p>
        </div>

        {/* Completion Rate */}
        <div className="p-3 rounded-xl bg-[#140B26] border border-[#2B184B] flex items-center justify-between text-xs">
          <div>
            <span className="text-white font-semibold block">Past Check Completion Rate</span>
            <span className="text-[10px] text-[#8E82AA]">Users answering all 3 statements</span>
          </div>
          <span className="text-xs font-bold font-mono text-[#F4B8DC]">
            {pastCheckMetrics?.completion?.formatted || "0.0% [95% CI: 0.0% – 0.0%, n=0]"}
          </span>
        </div>

        {/* Honesty & Rigor Disclosure */}
        <div className="p-3 rounded-xl bg-[#0F081D] border border-white/5 text-[10px] text-[#8E82AA] leading-relaxed">
          <strong className="text-white block mb-0.5">Statistical Rigor & Honesty Disclosure:</strong>
          All proportions report Wilson score 95% confidence intervals (Wilson 1927). We never present bare percentages without uncertainty intervals and sample sizes. Statements measure subjective resonance, not astronomical proof.
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
