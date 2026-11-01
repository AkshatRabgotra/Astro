import React, { useState } from "react";
import { Clock, Calendar, Sparkles, ChevronRight, Zap } from "lucide-react";
import { t } from "../i18n";

const PLANET_COLORS = {
  Sun: { bg: "bg-amber-500/20", border: "border-amber-500/50", text: "text-amber-300", accent: "#F59E0B" },
  Moon: { bg: "bg-cyan-500/20", border: "border-cyan-500/50", text: "text-cyan-300", accent: "#06B6D4" },
  Mars: { bg: "bg-rose-500/20", border: "border-rose-500/50", text: "text-rose-300", accent: "#F43F5E" },
  Rahu: { bg: "bg-purple-500/20", border: "border-purple-500/50", text: "text-purple-300", accent: "#A855F7" },
  Jupiter: { bg: "bg-yellow-500/20", border: "border-yellow-500/50", text: "text-yellow-300", accent: "#EAB308" },
  Saturn: { bg: "bg-blue-500/20", border: "border-blue-500/50", text: "text-blue-300", accent: "#3B82F6" },
  Mercury: { bg: "bg-emerald-500/20", border: "border-emerald-500/50", text: "text-emerald-300", accent: "#10B981" },
  Ketu: { bg: "bg-orange-500/20", border: "border-orange-500/50", text: "text-orange-300", accent: "#F97316" },
  Venus: { bg: "bg-pink-500/20", border: "border-pink-500/50", text: "text-pink-300", accent: "#EC4899" },
};

const DASHA_SIGNIFICANCE = {
  Sun: "Identity, authority, vitality, father, leadership, government recognition",
  Moon: "Emotions, peace of mind, mother, travel, public popularity, mental adaptability",
  Mars: "Ambition, courage, property, technical skill, drive, competitive victories",
  Rahu: "Worldly desire, sudden foreign opportunities, unorthodox innovation, sharp ambition",
  Jupiter: "Wisdom, expansion, financial gains, mentorship, dharma, child prosperity",
  Saturn: "Discipline, patience, career foundations, perseverance, reality check, service",
  Mercury: "Intellect, business acumen, communication, analytical pursuits, learning",
  Ketu: "Spiritual introspection, detachment, research, intuitive awakening, liberation",
  Venus: "Relationships, luxuries, arts, harmony, financial prosperity, public appeal",
};

export default function DashaTimeline({ chartFacts, lang = "en", onSelectDashaQuestion }) {
  const [selectedPeriod, setSelectedPeriod] = useState(null);

  if (!chartFacts || !chartFacts.current_dasha) {
    return null;
  }

  const currentDasha = chartFacts.current_dasha;
  const allDashas = chartFacts.all_dashas || [];
  const antardashas = chartFacts.antardashas || [];

  const activeMD = currentDasha.mahadasha_lord;
  const activeAD = currentDasha.antardasha_lord;

  const displayedPeriod = selectedPeriod || {
    lord: activeAD,
    parentLord: activeMD,
    isAntardasha: true,
    startDate: currentDasha.start_date,
    endDate: currentDasha.end_date,
    isCurrent: true,
  };

  const currentColors = PLANET_COLORS[displayedPeriod.lord] || PLANET_COLORS.Jupiter;

  return (
    <div className="crystal-card p-4 sm:p-5 relative overflow-hidden space-y-4">
      {/* Astrological Planetary Glyphs Watermark */}
      <div className="absolute -top-3 -right-3 text-4xl text-white/[0.04] select-none pointer-events-none font-serif">
        ☉ ☽ ♂ ♃
      </div>

      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-[#931B58] to-[#B21E68] text-white flex items-center justify-center shadow-md">
            <Clock className="w-4 h-4 text-[#FDE68A]" />
          </div>
          <div>
            <h3 className="font-serif text-sm sm:text-base font-bold text-white flex items-center gap-1.5">
              {t("dashaTitle", lang)}
            </h3>
            <p className="text-[11px] text-[#A299BC]">
              {t("dashaDesc", lang)}
            </p>
          </div>
        </div>
      </div>

      {/* Active Now Pill */}
      <div className="p-3 rounded-2xl bg-gradient-to-r from-[#1E1138] to-[#261545] border border-[#B21E68]/50 flex items-center justify-between shadow-lg">
        <div className="flex items-center gap-3">
          <div className="relative">
            <div className="w-3 h-3 rounded-full bg-[#E5A93C] animate-ping absolute" />
            <div className="w-3 h-3 rounded-full bg-[#E5A93C] relative" />
          </div>
          <div>
            <span className="text-[10px] uppercase font-semibold text-[#F4B8DC] tracking-wider block">
              {t("activePeriodNow", lang)}
            </span>
            <strong className="text-sm text-white font-serif">
              {activeMD} • {activeAD}
            </strong>
          </div>
        </div>
        <div className="text-right text-[11px] text-[#A299BC]">
          <span className="block font-mono text-white text-[11px]">{currentDasha.start_date}</span>
          <span className="text-[10px] text-[#7F739A]">{t("activeUntil", lang)} {currentDasha.end_date}</span>
        </div>
      </div>

      {/* 1. Mahadashas Horizontal Scrubber */}
      {allDashas.length > 0 && (
        <div className="space-y-1.5">
          <div className="flex items-center justify-between text-[11px] text-[#8E82AA] px-0.5">
            <span>Life Mahadasha Sequence</span>
            <span>Tap to inspect</span>
          </div>

          <div className="flex items-center gap-1.5 overflow-x-auto pb-2 scrollbar-none">
            {allDashas.map((md, idx) => {
              const isCurrent = md.mahadasha_lord === activeMD;
              const isSelected = displayedPeriod.lord === md.mahadasha_lord && !displayedPeriod.isAntardasha;
              const pColor = PLANET_COLORS[md.mahadasha_lord] || PLANET_COLORS.Sun;

              return (
                <button
                  key={idx}
                  onClick={() =>
                    setSelectedPeriod({
                      lord: md.mahadasha_lord,
                      parentLord: md.mahadasha_lord,
                      isAntardasha: false,
                      startDate: md.start_date,
                      endDate: md.end_date,
                      isCurrent,
                    })
                  }
                  className={`px-3 py-2 rounded-xl text-xs font-semibold whitespace-nowrap border transition-all flex flex-col items-center gap-0.5 shrink-0 ${
                    isCurrent
                      ? "bg-[#B21E68]/30 border-[#B21E68] text-white shadow-md shadow-[#B21E68]/20 ring-1 ring-[#F4B8DC]/40"
                      : isSelected
                      ? "bg-[#251842] border-[#F4B8DC] text-white"
                      : "bg-[#140D27] border-[#2A1D45] text-[#8E82AA] hover:text-white hover:border-[#4B3472]"
                  }`}
                >
                  <span className="font-serif text-xs">{md.mahadasha_lord}</span>
                  <span className="text-[9.5px] font-mono text-[#A299BC]">
                    {md.start_date?.slice(0, 4)}–{md.end_date?.slice(0, 4)}
                  </span>
                  {isCurrent && (
                    <span className="text-[8px] font-bold uppercase tracking-wider text-[#E5A93C] mt-0.5">
                      Current
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* 2. Antardashas Sub-Periods of Active Mahadasha */}
      {antardashas.length > 0 && (
        <div className="space-y-1.5 pt-1 border-t border-[#23173D]">
          <div className="flex items-center justify-between text-[11px] text-[#8E82AA] px-0.5">
            <span>Sub-Periods (Antardashas) of {activeMD} Mahadasha</span>
            <span className="text-[10px] text-[#E5A93C]">Active Sub-Cycle</span>
          </div>

          <div className="grid grid-cols-3 gap-1.5">
            {antardashas.map((ad, idx) => {
              const isCurrent = ad.antardasha_lord === activeAD;
              const isSelected = displayedPeriod.lord === ad.antardasha_lord && displayedPeriod.isAntardasha;

              return (
                <button
                  key={idx}
                  onClick={() =>
                    setSelectedPeriod({
                      lord: ad.antardasha_lord,
                      parentLord: ad.mahadasha_lord,
                      isAntardasha: true,
                      startDate: ad.start_date,
                      endDate: ad.end_date,
                      isCurrent,
                    })
                  }
                  className={`p-2 rounded-xl text-left border transition-all ${
                    isCurrent
                      ? "bg-gradient-to-tr from-[#931B58]/40 to-[#B21E68]/40 border-[#F4B8DC] text-white shadow-sm ring-1 ring-[#B21E68]"
                      : isSelected
                      ? "bg-[#23163E] border-[#E5A93C] text-white"
                      : "bg-[#140D26] border-[#271A3F] text-[#8A7EA6] hover:border-[#46316D]"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-serif text-xs font-bold text-white">
                      {ad.antardasha_lord}
                    </span>
                    {isCurrent && (
                      <span className="w-1.5 h-1.5 rounded-full bg-[#E5A93C] animate-pulse" />
                    )}
                  </div>
                  <div className="text-[9.5px] font-mono text-[#9B8EB9] mt-0.5 truncate">
                    {ad.start_date?.slice(2)} to {ad.end_date?.slice(2)}
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Selected Period Inspector Card */}
      <div className={`p-3.5 rounded-2xl border ${currentColors.bg} ${currentColors.border} space-y-2`}>
        <div className="flex items-center justify-between">
          <div>
            <span className="text-[10px] uppercase font-semibold text-[#A299BC] tracking-wider block">
              {displayedPeriod.isAntardasha ? "Antardasha Sub-Period" : "Major Mahadasha Phase"}
            </span>
            <h4 className="text-sm font-serif font-bold text-white">
              {displayedPeriod.isAntardasha
                ? `${displayedPeriod.parentLord}–${displayedPeriod.lord}`
                : `${displayedPeriod.lord} Mahadasha`}
            </h4>
          </div>
          <div className="text-right text-[11px] font-mono text-white">
            <span>{displayedPeriod.startDate}</span>
            <span className="text-[#8E82AA] block text-[10px]">to {displayedPeriod.endDate}</span>
          </div>
        </div>

        <p className="text-xs text-[#E1DBEF] leading-relaxed">
          <strong className="text-white">Karmic Theme: </strong>
          {DASHA_SIGNIFICANCE[displayedPeriod.lord] || "Major planetary activation and developmental timing."}
        </p>

        {/* 1-Tap Question Button */}
        {onSelectDashaQuestion && (
          <button
            onClick={() =>
              onSelectDashaQuestion(
                `How will my ${displayedPeriod.parentLord}–${displayedPeriod.lord} Dasha period (${displayedPeriod.startDate} to ${displayedPeriod.endDate}) shape my career, finances, and relationships?`
              )
            }
            className="w-full mt-2 py-2 px-3 rounded-xl bg-[#B21E68]/30 hover:bg-[#B21E68]/50 border border-[#B21E68]/60 text-xs font-semibold text-[#F4B8DC] flex items-center justify-center gap-1.5 transition-all active:scale-[0.98]"
          >
            <Sparkles className="w-3.5 h-3.5 text-[#E5A93C]" />
            <span>Ask reading about this Dasha window</span>
            <ChevronRight className="w-3.5 h-3.5" />
          </button>
        )}
      </div>
    </div>
  );
}
