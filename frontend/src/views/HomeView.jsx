import React from "react";
import { Sparkles, ArrowRight, Compass, Moon, Sun, Shield, Clock, Flame, Gift } from "lucide-react";
import KundliChart from "../components/KundliChart";
import DashaTimeline from "../components/DashaTimeline";
import TransitsCard from "../components/TransitsCard";
import { t } from "../i18n";

export default function HomeView({ chartFacts, profile, lang = "en", onSelectQuestion, onGoToAsk, onGoToRewards }) {
  const suggestedQuestions = [
    t("q1", lang),
    t("q2", lang),
    t("q3", lang),
    t("q4", lang),
  ];

  return (
    <div className="space-y-4 pb-28 max-w-md mx-auto px-4 pt-3">
      {/* Quick Ask Input Pill (Screenshot 1 & 2) */}
      <div 
        onClick={onGoToAsk}
        className="crystal-card p-2.5 pl-4 flex items-center justify-between cursor-pointer hover:border-[#B21E68] transition-all shadow-lg shadow-black/40 group relative"
      >
        <div className="flex items-center gap-2">
          <span className="text-amber-400 text-xs">✦</span>
          <span className="text-xs sm:text-sm text-[#BDB2D9] font-medium group-hover:text-white transition-colors">
            {t("quickAskPlaceholder", lang)}
          </span>
        </div>
        <div className="w-9 h-9 rounded-full bg-gradient-to-tr from-[#931B58] via-[#B21E68] to-[#E5A93C] text-white flex items-center justify-center shadow-md shadow-[#B21E68]/30 group-hover:scale-105 transition-transform shrink-0">
          <ArrowRight className="w-4 h-4" />
        </div>
      </div>

      {/* Daily Horoscope Card (Melooha Screenshot 1 - Crystal & Luminous) */}
      <div className="crystal-card p-5 relative overflow-hidden space-y-3">
        {/* Subtle Astrological Watermark Pattern */}
        <div className="absolute -top-6 -right-6 text-5xl text-white/[0.03] select-none pointer-events-none font-serif">
          ♈ ♌ ♐
        </div>

        <div className="flex items-center justify-between text-xs text-[#8E82AA]">
          <span className="font-semibold uppercase tracking-wider text-[#A299BC] flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-[#E5A93C] inline-block" />
            {t("dailyHoroscopeTitle", lang)}
          </span>
          <span className="astro-badge px-2.5 py-0.5 rounded-full text-[10.5px] font-semibold text-[#DDD5EE]">
            {t("today", lang)}
          </span>
        </div>

        <div className="flex items-center gap-4 my-1">
          {/* Circular Ring with Glow */}
          <div className="w-16 h-16 rounded-full border-4 border-[#B21E68] flex flex-col items-center justify-center text-white font-bold text-base shadow-lg shadow-[#B21E68]/50 cosmic-glow shrink-0 bg-[#160E28]">
            <span className="shimmer-text-plum">99%</span>
          </div>

          <div>
            <h3 className="font-serif text-lg font-bold text-white leading-snug">
              {t("horoscopeQuote", lang)}
            </h3>
            <div className="inline-flex items-center gap-2 mt-2 px-3 py-1 rounded-full astro-badge text-xs text-[#E1DBEF]">
              <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 inline-block shadow-sm shadow-cyan-400/50" />
              <span className="font-medium">{t("wearLightBlue", lang)}</span>
              <span className="text-[#685C83]">|</span>
              <span>{t("luckyNumber", lang)} <strong className="text-[#FDE68A]">2</strong></span>
            </div>
          </div>
        </div>
      </div>

      {/* Auspicious Muhurta / Choghadiya Card (Screenshot 1 - Golden Crystal) */}
      <div className="crystal-card-gold p-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-amber-500/20 border border-amber-400/40 text-[#FDE68A] shadow-md">
            <Clock className="w-5 h-5 text-[#E5A93C]" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-serif text-base font-bold text-white">{t("labhTitle", lang)}</span>
              <span className="text-[11px] px-2 py-0.5 rounded-full bg-[#B21E68]/30 border border-[#B21E68]/50 text-[#F4B8DC] font-semibold">
                {t("activeMuhurta", lang)}
              </span>
            </div>
            <p className="text-xs text-[#C7BEDC] mt-0.5">
              {t("labhDesc", lang)}
            </p>
          </div>
        </div>
      </div>

      {/* Daily Streak & Rewards Shortcut Banner (Screenshot 1) */}
      <div 
        onClick={onGoToRewards}
        className="crystal-card p-3.5 flex items-center justify-between cursor-pointer border border-[#E5A93C]/40 hover:border-[#E5A93C] transition-all group active:scale-98"
      >
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full gold-coin flex items-center justify-center text-amber-950 font-bold shrink-0">
            <Flame className="w-5 h-5 text-orange-950 fill-orange-900" />
          </div>
          <div>
            <h4 className="font-serif text-xs sm:text-sm font-bold text-white flex items-center gap-1.5">
              <span>{t("keepStreakTitle", lang)}</span>
              <span className="text-[10px] px-2 py-0.2 rounded bg-amber-400/20 text-[#FDE68A] font-bold">
                {t("dayRange", lang)}
              </span>
            </h4>
            <p className="text-[11px] text-[#A299BC] mt-0.5">
              {t("collectKarmaRewards", lang)}
            </p>
          </div>
        </div>

        <div className="w-7 h-7 rounded-full bg-[#271745] group-hover:bg-[#B21E68] text-[#F4B8DC] group-hover:text-white flex items-center justify-center transition-colors shrink-0">
          <ArrowRight className="w-3.5 h-3.5" />
        </div>
      </div>

      {/* Feature 1: Interactive Visual Kundli Chart Wheel */}
      {chartFacts && (
        <KundliChart
          chartFacts={chartFacts}
          lang={lang}
          onSelectHouseQuestion={onSelectQuestion}
        />
      )}

      {/* Feature 2: Interactive Vimshottari Dasha 120-Year Timeline Scrubber */}
      {chartFacts && (
        <DashaTimeline
          chartFacts={chartFacts}
          lang={lang}
          onSelectDashaQuestion={onSelectQuestion}
        />
      )}

      {/* Feature 4: Today's Live Planetary Transits (Gochara & Sade Sati) */}
      {profile && (
        <TransitsCard
          profile={profile}
          lang={lang}
          onSelectTransitQuestion={onSelectQuestion}
        />
      )}

      {/* Your Birth Chart Summary Card */}
      {chartFacts && (
        <div className="crystal-card p-5 space-y-3.5 relative overflow-hidden">
          <div className="absolute -bottom-8 -right-8 text-5xl text-white/[0.03] select-none pointer-events-none font-serif">
            ☉ ☽ ☿ ♀ ♂
          </div>

          <div className="flex items-center justify-between pb-2 border-b border-[#2C1D4A]">
            <div className="flex items-center gap-2">
              <Compass className="w-4 h-4 text-[#E5A93C]" />
              <h3 className="font-serif text-sm font-bold text-white">
                {t("vedicPlacements", lang)}
              </h3>
            </div>
            <span className="astro-badge px-2 py-0.5 rounded-full text-[10.5px] font-semibold text-[#DDD5EE]">
              {t("lahiriSidereal", lang)}
            </span>
          </div>

          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="p-3 rounded-xl astro-badge">
              <span className="text-[#8478A0] block text-[10px] font-medium">{t("ascendantLagna", lang)}</span>
              <span className="font-bold text-white text-xs mt-1 block truncate">
                {chartFacts.lagna_sign ? `${chartFacts.lagna_sign} (${chartFacts.formatted_lagna_degree})` : t("unavailable", lang)}
              </span>
            </div>

            <div className="p-3 rounded-xl astro-badge">
              <span className="text-[#8478A0] block text-[10px] font-medium">{t("moonNakshatra", lang)}</span>
              <span className="font-bold text-white text-xs mt-1 block truncate">
                {chartFacts.planets?.find(p => p.planet === "Moon")?.nakshatra?.name || "Moon"}
              </span>
            </div>

            {chartFacts.current_dasha && (
              <div className="p-3 rounded-xl astro-badge border-l-2 border-l-[#B21E68] col-span-2">
                <span className="text-[#8478A0] block text-[10px] font-medium">{t("activeDasha", lang)}</span>
                <span className="font-bold text-[#F4B8DC] text-xs mt-0.5 block">
                  {chartFacts.current_dasha.mahadasha_lord} • {chartFacts.current_dasha.antardasha_lord}
                </span>
                <span className="text-[10.5px] text-[#A299BC] block mt-0.5">
                  {t("activeUntil", lang)} {chartFacts.current_dasha.end_date}
                </span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Suggested Questions Section (Melooha Screenshot 3) */}
      <div className="crystal-card p-5 space-y-3">
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-[#E5A93C]" />
          <h3 className="font-serif text-sm font-bold text-white">
            {t("questionsForYou", lang)}
          </h3>
        </div>

        <div className="space-y-2">
          {suggestedQuestions.map((q, idx) => (
            <button
              key={idx}
              onClick={() => onSelectQuestion(q)}
              className="w-full text-left p-3 rounded-xl astro-badge hover:border-[#B21E68] hover:bg-[#22153E] transition-all flex items-center justify-between group active:scale-98"
            >
              <span className="text-xs text-[#E1DBEF] font-medium pr-2 group-hover:text-white transition-colors">
                {q}
              </span>
              <div className="w-7 h-7 rounded-full bg-[#271948] text-[#F4B8DC] group-hover:bg-[#B21E68] group-hover:text-white flex items-center justify-center shrink-0 transition-colors shadow-sm">
                <ArrowRight className="w-3.5 h-3.5" />
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
