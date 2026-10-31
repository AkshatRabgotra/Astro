import React from "react";
import { Sparkles, ArrowRight, Compass, Moon, Sun, Shield, Clock } from "lucide-react";

export default function HomeView({ chartFacts, onSelectQuestion, onGoToAsk }) {
  const suggestedQuestions = [
    "When will my career enter its strongest period?",
    "Will someone in my close circle betray my trust this year?",
    "What does my current Mahadasha say about relocating or finances?",
    "What spiritual practices will protect my energy right now?",
  ];

  return (
    <div className="space-y-4 pb-24 max-w-md mx-auto px-4 pt-3">
      {/* Quick Ask Input Pill (Screenshot 1) */}
      <div 
        onClick={onGoToAsk}
        className="glass-panel p-2.5 pl-4 flex items-center justify-between cursor-pointer hover:border-[#B21E68]/70 transition-all shadow-md group"
      >
        <span className="text-sm text-[#A299BC] font-medium group-hover:text-white transition-colors">
          Ask about exam, career or love...
        </span>
        <div className="w-9 h-9 rounded-full bg-gradient-to-tr from-[#931B58] to-[#B21E68] text-white flex items-center justify-center shadow-md">
          <ArrowRight className="w-4 h-4" />
        </div>
      </div>

      {/* Daily Horoscope Card (Melooha Screenshot 1) */}
      <div className="glass-panel p-5 relative overflow-hidden">
        <div className="flex items-center justify-between mb-3 text-xs text-[#8E82AA]">
          <span className="font-semibold uppercase tracking-wider text-[#A299BC]">Your Daily Horoscope</span>
          <span>Today</span>
        </div>

        <div className="flex items-center gap-4 my-2">
          {/* Circular Ring */}
          <div className="w-16 h-16 rounded-full border-4 border-[#B21E68] flex flex-col items-center justify-center text-white font-bold text-base shadow-lg shadow-[#B21E68]/30 shrink-0">
            <span>99%</span>
          </div>

          <div>
            <h3 className="font-serif text-lg font-semibold text-white leading-snug">
              Today a doubter comes around
            </h3>
            <div className="inline-flex items-center gap-2 mt-2 px-3 py-1 rounded-full bg-[#1A1230] border border-[#352554] text-xs text-[#E1DBEF]">
              <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 inline-block" />
              <span>Wear Light Blue</span>
              <span className="text-[#685C83]">|</span>
              <span>Lucky No. <strong>2</strong></span>
            </div>
          </div>
        </div>
      </div>

      {/* Auspicious Muhurta / Choghadiya Card (Screenshot 1) */}
      <div className="glass-panel p-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-[#E5A93C]/15 border border-[#E5A93C]/30 text-[#E5A93C]">
            <Clock className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-serif text-base font-semibold text-white">Labh</span>
              <span className="text-[11px] px-2 py-0.5 rounded bg-[#B21E68]/20 text-[#F4B8DC] font-medium">
                Active Muhurta
              </span>
            </div>
            <p className="text-xs text-[#A299BC] mt-0.5">
              A good hour for financial decisions and practical work.
            </p>
          </div>
        </div>
      </div>

      {/* Your Birth Chart Summary Card */}
      {chartFacts && (
        <div className="glass-panel p-5 space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-[#2B1E4A]">
            <div className="flex items-center gap-2">
              <Compass className="w-4 h-4 text-[#E5A93C]" />
              <h3 className="font-serif text-sm font-semibold text-white">
                Your Vedic Placements
              </h3>
            </div>
            <span className="text-[11px] text-[#A299BC]">Lahiri Sidereal</span>
          </div>

          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="p-2.5 rounded-xl bg-[#191130] border border-[#2F214F]">
              <span className="text-[#8478A0] block text-[10px]">Ascendant (Lagna)</span>
              <span className="font-semibold text-white text-xs mt-0.5 block truncate">
                {chartFacts.lagna_sign ? `${chartFacts.lagna_sign} (${chartFacts.formatted_lagna_degree})` : "Unavailable"}
              </span>
            </div>

            <div className="p-2.5 rounded-xl bg-[#191130] border border-[#2F214F]">
              <span className="text-[#8478A0] block text-[10px]">Moon Nakshatra</span>
              <span className="font-semibold text-white text-xs mt-0.5 block truncate">
                {chartFacts.planets?.find(p => p.planet === "Moon")?.nakshatra?.name || "Moon"}
              </span>
            </div>

            {chartFacts.current_dasha && (
              <div className="p-2.5 rounded-xl bg-[#191130] border border-[#B21E68]/30 col-span-2">
                <span className="text-[#8478A0] block text-[10px]">Current Vimshottari Dasha</span>
                <span className="font-semibold text-[#F4B8DC] text-xs mt-0.5 block">
                  {chartFacts.current_dasha.mahadasha_lord} Mahadasha • {chartFacts.current_dasha.antardasha_lord} Antardasha
                </span>
                <span className="text-[10px] text-[#A299BC] block mt-0.5">
                  Active until {chartFacts.current_dasha.end_date}
                </span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Suggested Questions Section (Melooha Screenshot 3) */}
      <div className="glass-panel p-5">
        <div className="flex items-center gap-2 mb-3">
          <Sparkles className="w-4 h-4 text-[#E5A93C]" />
          <h3 className="font-serif text-sm font-semibold text-white">
            Questions For You
          </h3>
        </div>

        <div className="space-y-2">
          {suggestedQuestions.map((q, idx) => (
            <button
              key={idx}
              onClick={() => onSelectQuestion(q)}
              className="w-full text-left p-3 rounded-xl bg-[#181130] border border-[#2F214F] hover:border-[#B21E68]/80 hover:bg-[#201440] transition-all flex items-center justify-between group"
            >
              <span className="text-xs text-[#E1DBEF] font-medium pr-2 group-hover:text-white transition-colors">
                {q}
              </span>
              <div className="w-7 h-7 rounded-full bg-[#271948] text-[#F4B8DC] group-hover:bg-[#B21E68] group-hover:text-white flex items-center justify-center shrink-0 transition-colors">
                <ArrowRight className="w-3.5 h-3.5" />
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
