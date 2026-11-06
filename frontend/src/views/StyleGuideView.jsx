import React, { useState } from "react";
import {
  Sparkles,
  ShieldCheck,
  Compass,
  Share2,
  AlertTriangle,
  RefreshCw,
  HelpCircle,
  Check,
  X,
  WifiOff,
  Clock,
  Layers,
  Palette,
  Type,
  Square,
  Maximize2,
  ChevronLeft,
} from "lucide-react";

export default function StyleGuideView({ onBack }) {
  const [activeSegment, setActiveSegment] = useState("chart");
  const [statementAnswer, setStatementAnswer] = useState(null);

  return (
    <div className="max-w-xl mx-auto px-4 pt-4 pb-28 space-y-8 text-left">
      {/* Top Header */}
      <div className="flex items-center justify-between pb-4 border-b border-[#2B184B]">
        <div className="flex items-center gap-2">
          {onBack && (
            <button
              onClick={onBack}
              className="p-2 rounded-xl bg-[#1A0E30] text-[#A299BC] hover:text-white"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
          )}
          <div>
            <div className="flex items-center gap-1.5">
              <span className="text-[10px] font-bold text-[#F4B8DC] uppercase tracking-wider block">
                Melooha Design System
              </span>
              <span className="px-1.5 py-0.2 rounded text-[9px] font-bold bg-amber-500/20 text-[#FDE68A] border border-amber-500/40">
                Admin Reference
              </span>
            </div>
            <h1 className="font-serif text-xl font-bold text-white flex items-center gap-2 mt-0.5">
              <Palette className="w-5 h-5 text-[#E5A93C]" />
              <span>UI Style Guide & States</span>
            </h1>
          </div>
        </div>
        <span className="text-xs px-2.5 py-1 rounded-full bg-[#1A0E30] text-[#E5A93C] border border-[#E5A93C]/40 font-mono">
          v1.2.0
        </span>
      </div>

      {/* 1. Design Tokens */}
      <section className="space-y-4">
        <h2 className="text-xs uppercase tracking-widest text-[#A299BC] font-bold flex items-center gap-2">
          <Palette className="w-4 h-4 text-[#F4B8DC]" />
          <span>1. Color & Design Tokens</span>
        </h2>

        {/* Color Palette Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 text-xs">
          <div className="p-3 rounded-2xl bg-[#080511] border border-[#2B184B] space-y-1">
            <div className="w-full h-8 rounded-lg bg-[#080511] border border-white/20" />
            <span className="text-white font-bold block">Cosmic Void</span>
            <span className="text-[10px] text-[#8E82AA] font-mono">#080511 (Canvas)</span>
          </div>
          <div className="p-3 rounded-2xl bg-[#140828] border border-[#2B184B] space-y-1">
            <div className="w-full h-8 rounded-lg bg-[#140828] border border-white/20" />
            <span className="text-white font-bold block">Nebula Surface</span>
            <span className="text-[10px] text-[#8E82AA] font-mono">#140828 (Card)</span>
          </div>
          <div className="p-3 rounded-2xl bg-[#140828] border border-[#2B184B] space-y-1">
            <div className="w-full h-8 rounded-lg bg-gradient-to-r from-[#931B58] to-[#B21E68]" />
            <span className="text-white font-bold block">Melooha Plum</span>
            <span className="text-[10px] text-[#8E82AA] font-mono">#931B58 &rarr; #B21E68</span>
          </div>
          <div className="p-3 rounded-2xl bg-[#140828] border border-[#2B184B] space-y-1">
            <div className="w-full h-8 rounded-lg bg-gradient-to-r from-[#E5A93C] to-[#FDE68A]" />
            <span className="text-white font-bold block">Radiant Gold</span>
            <span className="text-[10px] text-[#8E82AA] font-mono">#E5A93C &rarr; #FDE68A</span>
          </div>
        </div>

        {/* Typography & Radii */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
          <div className="crystal-card p-4 space-y-2">
            <span className="text-[#A299BC] font-semibold flex items-center gap-1.5">
              <Type className="w-3.5 h-3.5 text-[#E5A93C]" />
              Typography Stack
            </span>
            <div className="space-y-1.5">
              <div className="font-serif text-lg font-bold text-white">Serif: Cinzel / Playfair</div>
              <div className="font-sans text-xs text-[#C5B9DF]">Sans: Inter / Apple-System</div>
              <div className="font-mono text-xs text-[#FDE68A]">Mono: JetBrains / Consolas</div>
            </div>
          </div>

          <div className="crystal-card p-4 space-y-2">
            <span className="text-[#A299BC] font-semibold flex items-center gap-1.5">
              <Square className="w-3.5 h-3.5 text-cyan-400" />
              Radius & Spacing Scale
            </span>
            <div className="flex flex-wrap gap-2 text-[11px] text-[#C5B9DF]">
              <span className="px-2 py-1 bg-[#1E0F36] rounded-lg">lg (8px)</span>
              <span className="px-2 py-1 bg-[#1E0F36] rounded-xl">xl (12px)</span>
              <span className="px-2 py-1 bg-[#1E0F36] rounded-2xl">2xl (16px)</span>
              <span className="px-2 py-1 bg-[#1E0F36] rounded-3xl">3xl (24px)</span>
              <span className="px-2 py-1 bg-[#1E0F36] rounded-full">full (pill)</span>
            </div>
          </div>
        </div>
      </section>

      {/* 2. Atomic & Molecular Components */}
      <section className="space-y-4">
        <h2 className="text-xs uppercase tracking-widest text-[#A299BC] font-bold flex items-center gap-2">
          <Layers className="w-4 h-4 text-[#FDE68A]" />
          <span>2. Core Components</span>
        </h2>

        {/* 1. Top Bar & Balance Pill */}
        <div className="crystal-card p-4 space-y-3">
          <span className="text-[11px] text-[#A299BC] font-semibold block">Component: Top Bar & Balance Pill (Single Unit: Questions)</span>
          <div className="p-3 rounded-2xl bg-[#0B0616] border border-[#2B184B] flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full overflow-hidden p-0.5 bg-[#70033E] border border-[#B21E68]/60 flex items-center justify-center shrink-0">
                <img src="/melooha-logo.png" alt="Melooha" className="w-full h-full object-contain" />
              </div>
              <span className="font-serif font-bold text-sm text-white">Melooha</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="flex items-center gap-1.5 py-1 px-2.5 rounded-full bg-[#180C2E] border border-[#931B58]/50 text-xs">
                <Sparkles className="w-3.5 h-3.5 text-[#E5A93C]" />
                <span className="font-bold text-white">3</span>
                <span className="text-[10px] text-[#A299BC]">Questions</span>
              </div>
            </div>
          </div>
        </div>

        {/* 2. Chips & Evidence Chips */}
        <div className="crystal-card p-4 space-y-3">
          <span className="text-[11px] text-[#A299BC] font-semibold block">Component: Chips & Grounded Evidence Chips</span>
          <div className="flex flex-wrap gap-2">
            <span className="astro-badge px-2.5 py-1 rounded-full text-xs text-[#F4B8DC] font-medium">
              Lagna: Mesha
            </span>
            <span className="astro-badge px-2.5 py-1 rounded-full text-xs text-cyan-300 font-medium">
              Moon: Rohini
            </span>
            <span className="astro-badge px-2.5 py-1 rounded-full text-xs text-[#FDE68A] font-medium">
              Dasha: Jupiter
            </span>
            {/* Clickable Evidence Chip */}
            <button className="evidence-chip flex items-center gap-1.5 py-1 px-2.5 rounded-full bg-[#1E0E38] border border-[#B21E68]/60 text-xs text-white hover:border-[#E5A93C] transition-all">
              <Compass className="w-3.5 h-3.5 text-[#E5A93C]" />
              <span className="font-semibold">Jupiter in 9th House</span>
              <span className="text-[10px] text-[#A299BC]">| Fact #JUP_H9</span>
            </button>
          </div>
        </div>

        {/* 3. Segmented Control */}
        <div className="crystal-card p-4 space-y-3">
          <span className="text-[11px] text-[#A299BC] font-semibold block">Component: Segmented Control (Chart | Dasha | Transits)</span>
          <div className="p-1 rounded-2xl bg-[#140828] border border-[#2B184B] flex">
            {["chart", "dasha", "transits"].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveSegment(tab)}
                className={`flex-1 py-1.5 rounded-xl text-xs font-bold capitalize transition-all ${
                  activeSegment === tab
                    ? "bg-gradient-to-r from-[#931B58] to-[#B21E68] text-white shadow-md"
                    : "text-[#A299BC] hover:text-white"
                }`}
              >
                {tab}
              </button>
            ))}
          </div>
        </div>

        {/* 4. Past Check Statement Card (Yes / Not really / Can't recall) */}
        <div className="crystal-card p-4 space-y-3 border border-[#E5A93C]/40">
          <div className="flex items-center justify-between">
            <span className="text-[11px] text-[#E5A93C] font-semibold block">Component: Past Check Statement Card (44px Touch Targets)</span>
            <span className="text-[10px] text-[#A299BC]">Reflection, Not Proof</span>
          </div>

          <div className="p-4 rounded-2xl bg-[#160B2C] border border-[#2D1B50] space-y-4">
            <p className="font-serif text-sm font-semibold text-white leading-relaxed">
              "Around March 2021, did something in your career or work direction shift noticeably for you?"
            </p>
            <div className="grid grid-cols-3 gap-2">
              <button
                onClick={() => setStatementAnswer("yes")}
                className={`min-h-[44px] py-2 px-3 rounded-xl border text-xs font-bold flex items-center justify-center gap-1.5 transition-all ${
                  statementAnswer === "yes"
                    ? "bg-emerald-600 border-emerald-400 text-white"
                    : "bg-[#1F103A] border-emerald-500/30 text-emerald-300 hover:bg-emerald-500/10"
                }`}
              >
                <Check className="w-3.5 h-3.5" />
                <span>Yes</span>
              </button>
              <button
                onClick={() => setStatementAnswer("not_really")}
                className={`min-h-[44px] py-2 px-3 rounded-xl border text-xs font-bold flex items-center justify-center gap-1.5 transition-all ${
                  statementAnswer === "not_really"
                    ? "bg-rose-600 border-rose-400 text-white"
                    : "bg-[#1F103A] border-rose-500/30 text-rose-300 hover:bg-rose-500/10"
                }`}
              >
                <X className="w-3.5 h-3.5" />
                <span>Not really</span>
              </button>
              <button
                onClick={() => setStatementAnswer("cant_recall")}
                className={`min-h-[44px] py-2 px-3 rounded-xl border text-xs font-bold flex items-center justify-center gap-1.5 transition-all ${
                  statementAnswer === "cant_recall"
                    ? "bg-amber-600 border-amber-400 text-white"
                    : "bg-[#1F103A] border-amber-500/30 text-amber-300 hover:bg-amber-500/10"
                }`}
              >
                <HelpCircle className="w-3.5 h-3.5" />
                <span>Can't recall</span>
              </button>
            </div>
          </div>
        </div>

        {/* 5. Share Button */}
        <div className="crystal-card p-4 space-y-3">
          <span className="text-[11px] text-[#A299BC] font-semibold block">Component: Action & Share Buttons (44px Touch Targets)</span>
          <div className="flex gap-2">
            <button className="flex-1 min-h-[44px] py-2.5 px-4 rounded-2xl bg-gradient-to-r from-[#931B58] via-[#B21E68] to-[#E5A93C] text-white font-bold text-xs shadow-lg flex items-center justify-center gap-2 hover:brightness-110 active:scale-95 transition-all">
              <Share2 className="w-4 h-4" />
              <span>Share Dasha Twin Card</span>
            </button>
            <button className="min-h-[44px] py-2.5 px-4 rounded-2xl bg-[#20103A] border border-[#3C1D6B] text-xs font-bold text-[#C5B9DF] hover:text-white flex items-center justify-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-[#E5A93C]" />
              <span>Another parallel</span>
            </button>
          </div>
        </div>
      </section>

      {/* 3. Comprehensive States Catalog (B7 Explicit Requirement) */}
      <section className="space-y-4">
        <h2 className="text-xs uppercase tracking-widest text-[#A299BC] font-bold flex items-center gap-2">
          <Maximize2 className="w-4 h-4 text-cyan-400" />
          <span>3. Complete State Documentation</span>
        </h2>

        {/* State 1: Loading Skeleton */}
        <div className="crystal-card p-4 space-y-2">
          <span className="text-[11px] font-bold text-[#A299BC] uppercase">State 1: Loading Skeleton</span>
          <div className="p-4 rounded-2xl bg-[#140828] border border-[#2B184B] space-y-3 animate-pulse">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-purple-900/40" />
              <div className="space-y-1.5 flex-1">
                <div className="h-3 w-1/3 bg-purple-900/40 rounded" />
                <div className="h-2.5 w-1/2 bg-purple-900/20 rounded" />
              </div>
            </div>
            <div className="h-4 w-full bg-purple-900/30 rounded" />
            <div className="h-4 w-4/5 bg-purple-900/20 rounded" />
          </div>
        </div>

        {/* State 2: Empty State */}
        <div className="crystal-card p-4 space-y-2">
          <span className="text-[11px] font-bold text-[#A299BC] uppercase">State 2: Empty State</span>
          <div className="p-6 rounded-2xl bg-[#140828] border border-[#2B184B] text-center space-y-2">
            <div className="w-10 h-10 rounded-full bg-purple-950/60 border border-purple-800/40 flex items-center justify-center text-[#A299BC] mx-auto">
              <HelpCircle className="w-5 h-5 text-[#F4B8DC]" />
            </div>
            <h4 className="font-serif text-xs font-bold text-white">No Previous Questions Yet</h4>
            <p className="text-[10.5px] text-[#8E82AA] max-w-xs mx-auto">
              Ask your first grounded astrological question to see it saved in your reading timeline.
            </p>
          </div>
        </div>

        {/* State 3: Error State with Retry */}
        <div className="crystal-card p-4 space-y-2">
          <span className="text-[11px] font-bold text-[#A299BC] uppercase">State 3: Error State (with Retry)</span>
          <div className="p-4 rounded-2xl bg-rose-950/20 border border-rose-500/30 flex items-center justify-between gap-3 text-xs">
            <div className="flex items-center gap-2 text-rose-300">
              <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
              <span>Could not compute dasha timeline. Check birth inputs.</span>
            </div>
            <button className="py-1.5 px-3 rounded-xl bg-rose-500/20 hover:bg-rose-500/30 text-rose-200 font-bold flex items-center gap-1.5 shrink-0">
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Retry</span>
            </button>
          </div>
        </div>

        {/* State 4: Offline State */}
        <div className="crystal-card p-4 space-y-2">
          <span className="text-[11px] font-bold text-[#A299BC] uppercase">State 4: Offline State</span>
          <div className="p-3.5 rounded-2xl bg-amber-500/10 border border-amber-500/30 flex items-center gap-2.5 text-xs text-amber-200">
            <WifiOff className="w-4 h-4 text-amber-400 shrink-0" />
            <div className="leading-tight">
              <span className="font-bold text-amber-300 block">Offline Mode Active</span>
              <span className="text-[10px] text-amber-200/80">Cached Swiss Ephemeris chart facts and saved readings remain fully readable.</span>
            </div>
          </div>
        </div>

        {/* State 5: Zero-Balance Paywall State */}
        <div className="crystal-card p-4 space-y-2">
          <span className="text-[11px] font-bold text-[#A299BC] uppercase">State 5: Zero-Balance State</span>
          <div className="p-4 rounded-2xl bg-[#1A0A2E] border border-[#B21E68]/50 flex items-center justify-between text-xs">
            <div className="space-y-0.5">
              <span className="font-bold text-white flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-rose-400" />
                0 Questions Remaining
              </span>
              <span className="text-[10px] text-[#A299BC]">Top up 5 free questions or complete daily streak.</span>
            </div>
            <button className="py-2 px-3.5 rounded-xl bg-gradient-to-r from-[#931B58] to-[#E5A93C] text-white font-bold text-xs shadow-md">
              Add Questions Free
            </button>
          </div>
        </div>

        {/* State 6: Unknown Birth Time State */}
        <div className="crystal-card p-4 space-y-2">
          <span className="text-[11px] font-bold text-[#A299BC] uppercase">State 6: Unknown Birth Time State</span>
          <div className="p-3.5 rounded-2xl bg-[#160E2A] border border-[#3B2266] space-y-2 text-xs">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5 text-white font-semibold">
                <Clock className="w-3.5 h-3.5 text-[#E5A93C]" />
                <span>Time-Independent Mode (Chandra Lagna)</span>
              </div>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 border border-amber-400/30 font-semibold">
                Approximate
              </span>
            </div>
            <p className="text-[10.5px] text-[#A299BC] leading-relaxed">
              When exact birth time is unverified, Ascendant (Lagna) is hidden to prevent false precision. Calculations switch to Chandra Lagna (Moon chart) and Mahadasha-level analysis only.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}
