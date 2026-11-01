import React from "react";
import { X, Compass, Sparkles, CheckCircle2, ShieldCheck, Calendar, Activity } from "lucide-react";

export default function EvidenceModal({ fact, onClose }) {
  if (!fact) return null;

  const meta = fact.metadata || {};

  return (
    <div 
      className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/80 backdrop-blur-md p-0 sm:p-4 transition-all"
      onClick={onClose}
    >
      <div 
        className="w-full max-w-lg crystal-card border-[#B21E68]/60 rounded-t-3xl sm:rounded-3xl p-6 shadow-2xl relative animate-in slide-in-from-bottom duration-200 space-y-4"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Handle for mobile drawer */}
        <div className="w-12 h-1 bg-[#453664] rounded-full mx-auto mb-2 sm:hidden" />

        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-[#2D1F4D]">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-[#B21E68]/20 border border-[#B21E68]/40 text-[#F4B8DC]">
              <Compass className="w-5 h-5 text-[#E5A93C]" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono font-semibold px-2 py-0.5 rounded bg-[#B21E68]/30 text-[#F4B8DC] border border-[#B21E68]/40">
                  {fact.id}
                </span>
                <span className="text-xs uppercase tracking-wider text-[#A299BC] font-medium">
                  {fact.category} Fact
                </span>
              </div>
              <h3 className="font-serif text-lg font-semibold text-white mt-0.5">
                {fact.subject}
              </h3>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="p-2 rounded-full text-[#A299BC] hover:text-white hover:bg-white/10 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Fact Statement */}
        <div className="my-4 p-3.5 rounded-xl bg-[#1C1438] border border-[#3A275E]">
          <p className="text-sm text-[#E2DCF0] leading-relaxed font-medium">
            "{fact.text}"
          </p>
        </div>

        {/* Astronomical Breakdown Grid */}
        <div className="grid grid-cols-2 gap-2.5 my-4 text-xs">
          {meta.sign && (
            <div className="p-3 rounded-xl bg-[#181030] border border-[#2F214F]">
              <span className="text-[#8E82AA] block mb-1">Zodiac Sign (Rashi)</span>
              <span className="text-white font-medium text-sm flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-[#E5A93C]" />
                {meta.sign} {meta.sign_number ? `(${meta.sign_number}/12)` : ""}
              </span>
            </div>
          )}

          {meta.house !== undefined && (
            <div className="p-3 rounded-xl bg-[#181030] border border-[#2F214F]">
              <span className="text-[#8E82AA] block mb-1">Whole-Sign House</span>
              <span className="text-white font-medium text-sm">
                {meta.house ? `House ${meta.house}` : "Unavailable (Birth time unknown)"}
              </span>
            </div>
          )}

          {meta.formatted_degree && (
            <div className="p-3 rounded-xl bg-[#181030] border border-[#2F214F]">
              <span className="text-[#8E82AA] block mb-1">Coordinate</span>
              <span className="text-white font-medium text-sm font-mono">
                {meta.formatted_degree}
              </span>
            </div>
          )}

          {meta.nakshatra && (
            <div className="p-3 rounded-xl bg-[#181030] border border-[#2F214F]">
              <span className="text-[#8E82AA] block mb-1">Nakshatra & Pada</span>
              <span className="text-white font-medium text-sm">
                {meta.nakshatra} {meta.nakshatra_pada ? `(P${meta.nakshatra_pada})` : ""}
              </span>
            </div>
          )}

          {meta.is_retrograde && (
            <div className="p-3 rounded-xl bg-[#181030] border border-[#E5A93C]/40 text-[#E5A93C]">
              <span className="block mb-1 opacity-80">Motion</span>
              <span className="font-semibold text-sm">Retrograde (Vakri)</span>
            </div>
          )}

          {meta.is_exalted && (
            <div className="p-3 rounded-xl bg-[#181030] border border-emerald-500/40 text-emerald-300">
              <span className="block mb-1 opacity-80">Dignity</span>
              <span className="font-semibold text-sm">Exalted (Uccha)</span>
            </div>
          )}

          {meta.is_debilitated && (
            <div className="p-3 rounded-xl bg-[#181030] border border-rose-500/40 text-rose-300">
              <span className="block mb-1 opacity-80">Dignity</span>
              <span className="font-semibold text-sm">Debilitated (Neecha)</span>
            </div>
          )}

          {meta.mahadasha && (
            <div className="p-3 rounded-xl bg-[#181030] border border-[#B21E68]/40 col-span-2">
              <span className="text-[#8E82AA] block mb-1 flex items-center gap-1">
                <Calendar className="w-3.5 h-3.5 text-[#F4B8DC]" />
                Vimshottari Dasha Window
              </span>
              <span className="text-white font-medium text-sm">
                {meta.mahadasha} / {meta.antardasha} ({meta.start_date} → {meta.end_date})
              </span>
            </div>
          )}
        </div>

        {/* Grounding Seal */}
        <div className="flex items-center gap-2 pt-3 border-t border-[#2D1F4D] text-[#A299BC] text-xs">
          <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>
            100% Grounded fact computed via Swiss Ephemeris (Lahiri Sidereal).
          </span>
        </div>
      </div>
    </div>
  );
}
