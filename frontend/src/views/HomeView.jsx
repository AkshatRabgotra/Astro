import React, { useState } from "react";
import {
  Sparkles,
  ArrowRight,
  Clock,
  Flame,
  Calendar,
  Sun,
  CheckCircle2,
  AlertCircle,
  ExternalLink,
  Download,
  Bell,
  RotateCcw,
} from "lucide-react";
import DashaTwinCard from "../components/DashaTwinCard";
import { getPersonalizedDailyInsights } from "../utils/vedicDaily";
import { useTypewriter } from "../utils/useTypewriter";
import { t } from "../i18n";

const HOME_ASK_PHRASES = {
  en: [
    "Ask about exam, career, or love...",
    "When will my career enter its strongest period?",
    "What does my 7th house reveal about marriage?",
    "Is this year auspicious for property investment?",
    "How is my active Mahadasha affecting me?",
    "When will financial stability and growth arrive?",
    "Which gemstone strengthens my Lagna lord?",
  ],
  hi: [
    "परीक्षा, करियर या प्रेम के बारे में पूछें...",
    "मेरा करियर कब सबसे मजबूत दौर में प्रवेश करेगा?",
    "सप्तम भाव मेरे विवाह और रिश्ते के बारे में क्या कहता है?",
    "क्या यह वर्ष नए व्यवसाय या संपत्ति के लिए शुभ है?",
    "मेरी वर्तमान महादशा जीवन में क्या परिवर्तन ला रही है?",
    "आर्थिक स्थिरता और धन लाभ का योग कब बनेगा?",
  ],
};

const PRESET_MUHURTA_QUERIES = [
  "Starting my new tech venture next week in Bengaluru",
  "Griha Pravesh ceremony in Austin next month",
  "Buying a new vehicle this Friday in Mumbai",
  "Signing international business contract next Tuesday",
  "Auspicious time for investing & trading in New Delhi",
];

export default function HomeView({
  user,
  chartFacts,
  profile,
  lang = "en",
  onSelectQuestion,
  onGoToAsk,
  onGoToRewards,
}) {
  const suggestedQuestions = [
    t("q1", lang),
    t("q2", lang),
    t("q3", lang),
    t("q4", lang),
  ];

  // Animated Typewriter sentence former & backspacer for Quick Ask pill
  const homePhrases = HOME_ASK_PHRASES[lang] || HOME_ASK_PHRASES.en;
  const animatedQuickAskText = useTypewriter(homePhrases, {
    typingSpeed: 60,
    deletingSpeed: 30,
    pauseMs: 2000,
    emptyPauseMs: 380,
  });

  // Muhurta State right on the Home Page
  const [muhurtaQuery, setMuhurtaQuery] = useState("");
  const [muhurtaLoading, setMuhurtaLoading] = useState(false);
  const [muhurtaResult, setMuhurtaResult] = useState(null);
  const [muhurtaError, setMuhurtaError] = useState(null);
  const [selectedSlotIndex, setSelectedSlotIndex] = useState(0);
  const [alertSuccess, setAlertSuccess] = useState(false);
  const [suggestionIndex, setSuggestionIndex] = useState(0);
  const [fadeAnim, setFadeAnim] = useState(true);

  // Rotating suggestion inside text area that smoothly fades in and out
  React.useEffect(() => {
    const interval = setInterval(() => {
      setFadeAnim(false);
      setTimeout(() => {
        setSuggestionIndex((prev) => (prev + 1) % PRESET_MUHURTA_QUERIES.length);
        setFadeAnim(true);
      }, 350);
    }, 3200);
    return () => clearInterval(interval);
  }, []);

  const activeName = profile?.name || user?.name || "You";
  const moonPlanet = chartFacts?.planets?.find((p) => p.planet === "Moon");
  const janmaNakshatra = moonPlanet?.nakshatra?.name;
  const janmaRashi = moonPlanet?.sign;

  // Personalized Daily Insights (DOB, Moon Sign, real-time Choghadiya)
  const dailyInsights = getPersonalizedDailyInsights(profile, chartFacts, lang);

  const handleCalculateMuhurta = async (queryString) => {
    const qText = (queryString || muhurtaQuery).trim();
    if (!qText) return;

    setMuhurtaLoading(true);
    setMuhurtaError(null);
    setAlertSuccess(false);

    try {
      const res = await fetch("/api/muhurta/plan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: user?.id,
          profile_id: profile?.id,
          query: qText,
          location_name: profile?.place_name,
          latitude: profile?.latitude,
          longitude: profile?.longitude,
          timezone_str: profile?.timezone_str,
        }),
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Failed to calculate Muhurta");
      }

      const data = await res.json();
      setMuhurtaResult(data);
      setSelectedSlotIndex(0);
    } catch (err) {
      setMuhurtaError(err.message || "Failed to calculate auspicious window.");
    } finally {
      setMuhurtaLoading(false);
    }
  };

  const handleScheduleAlert = async (muhurtaId) => {
    try {
      const res = await fetch(`/api/muhurta/${muhurtaId}/schedule-alert`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ channel: "push" }),
      });
      if (res.ok) {
        setAlertSuccess(true);
        setTimeout(() => setAlertSuccess(false), 4000);
      }
    } catch (_) {}
  };

  const handleDownloadIcs = (muhurtaId, rank) => {
    window.location.href = `/api/muhurta/${muhurtaId}/ics?slot_rank=${rank}`;
  };

  return (
    <div className="space-y-4 pb-28 max-w-md mx-auto px-4 pt-3">
      {/* Quick Ask Input Pill - Luminous Faded Crystal with Typewriter Animation */}
      <div
        onClick={onGoToAsk}
        className="p-2.5 pl-4 flex items-center justify-between cursor-pointer rounded-2xl bg-white/[0.10] hover:bg-white/[0.15] border border-white/25 hover:border-white/40 backdrop-blur-xl shadow-[0_8px_32px_rgba(0,0,0,0.5),inset_0_1px_1px_rgba(255,255,255,0.2)] transition-all group relative overflow-hidden"
      >
        <div className="flex items-center gap-2.5 min-w-0 flex-1 mr-2">
          <span className="text-amber-400 text-sm shrink-0">✦</span>
          <span className="text-xs sm:text-sm text-white font-semibold group-hover:text-amber-200 transition-colors drop-shadow-sm truncate flex items-center min-h-[20px]">
            {animatedQuickAskText || "\u00A0"}
            <span className="inline-block w-1.5 h-3.5 bg-amber-300 ml-1 rounded-[1px] animate-pulse shrink-0" />
          </span>
        </div>
        <div className="w-9 h-9 rounded-full bg-gradient-to-tr from-[#931B58] via-[#B21E68] to-[#E5A93C] text-white flex items-center justify-center shadow-md shadow-[#B21E68]/40 group-hover:scale-105 transition-transform shrink-0">
          <ArrowRight className="w-4 h-4" />
        </div>
      </div>

      {/* Daily Horoscope Card - Precision Astrological Alignment */}
      <div className="crystal-card p-5 relative overflow-hidden space-y-3.5 border border-[#B21E68]/40 shadow-[0_16px_40px_rgba(0,0,0,0.7)]">
        {/* Visible Celestial Constellation & Sacred Geometry Watermark SVG */}
        <svg
          className="absolute -right-6 -bottom-6 w-48 h-48 text-[#F4B8DC]/15 pointer-events-none select-none"
          viewBox="0 0 160 160"
          fill="none"
          stroke="currentColor"
        >
          <circle cx="80" cy="80" r="74" strokeWidth="0.75" strokeDasharray="3 3" />
          <circle cx="80" cy="80" r="54" strokeWidth="0.5" />
          <circle cx="80" cy="80" r="34" strokeWidth="0.75" strokeDasharray="2 3" />
          <circle cx="80" cy="80" r="14" strokeWidth="0.5" />
          <line x1="6" y1="80" x2="154" y2="80" strokeWidth="0.5" strokeOpacity="0.4" />
          <line x1="80" y1="6" x2="80" y2="154" strokeWidth="0.5" strokeOpacity="0.4" />
          <line x1="28" y1="28" x2="132" y2="132" strokeWidth="0.5" strokeOpacity="0.3" />
          <line x1="28" y1="132" x2="132" y2="28" strokeWidth="0.5" strokeOpacity="0.3" />
          <circle cx="80" cy="6" r="2.5" fill="#E5A93C" fillOpacity="0.8" />
          <circle cx="154" cy="80" r="2.5" fill="#F4B8DC" fillOpacity="0.8" />
          <circle cx="132" cy="28" r="2" fill="#DDD5EE" fillOpacity="0.7" />
          <circle cx="28" cy="132" r="2" fill="#DDD5EE" fillOpacity="0.7" />
          <circle cx="80" cy="80" r="3.5" fill="#E5A93C" fillOpacity="0.9" />
        </svg>

        {/* Visible Zodiac Glyph Constellation Belt */}
        <div className="absolute top-2.5 right-3.5 text-xs font-serif text-[#E5A93C]/30 tracking-widest select-none pointer-events-none">
          ♈ ♌ ♐ ♓ ♉
        </div>

        <div className="flex items-center justify-between text-xs text-[#8E82AA] relative z-10">
          <span className="font-semibold uppercase tracking-wider text-[#A299BC] flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-[#E5A93C] inline-block shadow-sm shadow-amber-400/50" />
            {t("dailyHoroscopeTitle", lang)}
          </span>
          <span className="astro-badge px-2.5 py-0.5 rounded-full text-[10px] font-semibold text-[#DDD5EE] flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            <span>{t("today", lang)} • {dailyInsights.varaText.split(" ")[0]}</span>
          </span>
        </div>

        <div className="flex items-start sm:items-center gap-3.5 my-1 relative z-10">
          <div className="w-16 h-16 rounded-full border-4 border-[#B21E68] flex flex-col items-center justify-center text-white font-bold text-base shadow-lg shadow-[#B21E68]/60 cosmic-glow shrink-0 bg-[#160E28] mt-0.5 sm:mt-0">
            <span className="shimmer-text-plum">{dailyInsights.harmonyPercent}%</span>
          </div>

          <div className="flex-1 min-w-0 space-y-2">
            <h3 className="font-serif text-sm sm:text-base font-bold text-white leading-snug break-words">
              {dailyInsights.horoscopeQuote}
            </h3>
            <div className="inline-flex flex-wrap items-center gap-2 px-3 py-1 rounded-full astro-badge text-xs text-[#E1DBEF]">
              <span
                className="w-2.5 h-2.5 rounded-full inline-block shadow-sm shrink-0"
                style={{ backgroundColor: dailyInsights.luckyColorHex }}
              />
              <span className="font-medium whitespace-nowrap">
                {lang === "hi" ? "शुभ रंग: " : "Wear "}{dailyInsights.luckyColor}
              </span>
              <span className="text-[#685C83]">|</span>
              <span className="whitespace-nowrap">
                {lang === "hi" ? "शुभ अंक: " : "Lucky No. "}
                <strong className="text-[#FDE68A]">{dailyInsights.luckyNumber}</strong>
              </span>
            </div>
          </div>
        </div>

        {/* Astronomical Precision Micro-Bar (Fully Responsive, Zero-Overlap) */}
        <div className="pt-2.5 border-t border-[#3A184A]/60 flex flex-wrap items-center justify-between gap-x-2 gap-y-1.5 text-[10px] text-[#A299BC] relative z-10">
          <span className="font-mono text-[#E5A93C] min-w-0 flex-1 basis-[160px] truncate text-[10.5px]">
            {dailyInsights.nakshatraWithPada}
          </span>
          <span className="text-[9.5px] font-mono text-[#DDD5EE] bg-[#220D32] px-2.5 py-0.5 rounded-lg border border-[#522064] shrink-0 self-center">
            {dailyInsights.ayanamsaPrecision}
          </span>
        </div>
      </div>

      {/* Real-time Dynamic Active Muhurta / Choghadiya Banner */}
      <div className="crystal-card-gold p-4 flex items-center justify-between border border-[#E5A93C]/40 relative overflow-hidden">
        {/* Subtle Solar Horizon Rays SVG */}
        <svg
          className="absolute -right-4 -bottom-4 w-28 h-28 text-amber-500/10 pointer-events-none select-none"
          viewBox="0 0 100 100"
          fill="none"
          stroke="currentColor"
        >
          <circle cx="50" cy="50" r="40" strokeWidth="0.75" strokeDasharray="2 3" />
          <line x1="50" y1="10" x2="50" y2="90" strokeWidth="0.5" />
          <line x1="10" y1="50" x2="90" y2="50" strokeWidth="0.5" />
          <circle cx="50" cy="50" r="16" strokeWidth="0.5" />
        </svg>

        <div className="flex items-center gap-3 relative z-10">
          <div className="p-2.5 rounded-xl bg-amber-500/20 border border-amber-400/40 text-[#FDE68A] shadow-md shrink-0">
            <Clock className="w-5 h-5 text-[#E5A93C]" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-serif text-base font-bold text-white">
                {dailyInsights.activeMuhurtaTitle}
              </span>
              <span
                className={`text-[11px] px-2 py-0.5 rounded-full border font-semibold ${
                  dailyInsights.isAuspiciousMuhurta
                    ? "bg-emerald-500/20 border-emerald-500/40 text-emerald-300"
                    : "bg-amber-500/20 border-amber-500/40 text-amber-300"
                }`}
              >
                {lang === "hi" ? "सक्रिय चौघड़िया" : "Active Muhurta"}
              </span>
            </div>
            <p className="text-xs text-[#C7BEDC] mt-0.5">
              {dailyInsights.activeMuhurtaDesc}
            </p>
          </div>
        </div>
      </div>

      {/* ======================================================== */}
      {/* 🌟 NATIVE AUSPICIOUS MUHURTA PLANNER (COMPACT & MINIMAL)*/}
      {/* ======================================================== */}
      <div className="crystal-card p-3.5 space-y-2.5 relative overflow-hidden border border-[#E5A93C]/40 shadow-lg bg-gradient-to-b from-[#1C0F2D] via-[#160B24] to-[#12081E]">
        {/* Celestial Quadrant Watermark SVG */}
        <svg
          className="absolute -right-4 -bottom-4 w-32 h-32 text-amber-500/10 pointer-events-none select-none"
          viewBox="0 0 100 100"
          fill="none"
          stroke="currentColor"
        >
          <path d="M 10 90 A 80 80 0 0 1 90 10" strokeWidth="0.75" strokeDasharray="3 3" />
          <path d="M 30 90 A 60 60 0 0 1 90 30" strokeWidth="0.5" />
          <line x1="10" y1="90" x2="90" y2="90" strokeWidth="0.5" />
          <line x1="90" y1="90" x2="90" y2="10" strokeWidth="0.5" />
          <line x1="10" y1="90" x2="90" y2="10" strokeWidth="0.5" strokeOpacity="0.4" />
        </svg>

        {/* Header - Sleek & Inline */}
        <div className="flex items-center justify-between relative z-10">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-lg bg-amber-500/20 border border-amber-400/40 flex items-center justify-center text-amber-300">
              <Calendar className="w-3.5 h-3.5" />
            </div>
            <h4 className="font-serif text-xs sm:text-sm font-bold text-white">
              {lang === "hi" ? "शुभ मुहूर्त प्लानर" : "Auspicious Muhurta"}
            </h4>
          </div>
          {activeName && (
            <span className="text-[10px] font-mono text-[#E5A93C] bg-[#241038] px-2 py-0.5 rounded-full border border-[#4C2068]">
              {activeName} {janmaNakshatra ? `• ${janmaNakshatra}` : ""}
            </span>
          )}
        </div>

        {/* Minimal Faded Frosted Input Pill with Rotating Suggestion */}
        <div className="relative flex items-center bg-white/[0.10] hover:bg-white/[0.15] rounded-2xl pl-3 pr-1.5 py-1.5 border border-white/25 shadow-inner backdrop-blur-xl transition-colors z-10">
          <Sparkles className="w-4 h-4 text-amber-400 shrink-0 mr-2" />
          
          <div className="relative flex-1 flex items-center min-w-0 h-8">
            <input
              type="text"
              value={muhurtaQuery}
              onChange={(e) => setMuhurtaQuery(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  handleCalculateMuhurta(muhurtaQuery || PRESET_MUHURTA_QUERIES[suggestionIndex]);
                }
              }}
              className="w-full bg-transparent text-white text-xs font-semibold focus:outline-none z-10 py-1"
            />
            {!muhurtaQuery && (
              <span
                onClick={() => {
                  const val = PRESET_MUHURTA_QUERIES[suggestionIndex];
                  setMuhurtaQuery(val);
                }}
                className={`absolute left-0 text-xs text-white/95 font-medium select-none cursor-pointer truncate max-w-full drop-shadow-sm transition-opacity duration-300 ${
                  fadeAnim ? "opacity-100" : "opacity-0"
                }`}
              >
                {PRESET_MUHURTA_QUERIES[suggestionIndex]}
              </span>
            )}
          </div>

          <button
            onClick={() => handleCalculateMuhurta(muhurtaQuery || PRESET_MUHURTA_QUERIES[suggestionIndex])}
            disabled={muhurtaLoading}
            className="w-8 h-8 rounded-full bg-gradient-to-tr from-[#931B58] via-[#B21E68] to-[#E5A93C] text-white flex items-center justify-center shadow-md hover:scale-105 active:scale-95 transition-all shrink-0 ml-1.5"
            title="Calculate Muhurta"
          >
            {muhurtaLoading ? (
              <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
            ) : (
              <ArrowRight className="w-4 h-4" />
            )}
          </button>
        </div>

        {/* Minimal Subtle Suggestion Chips (Single line) */}
        <div className="flex items-center gap-1.5 pt-0.5 text-[10px] text-[#A299BC] overflow-x-auto no-scrollbar relative z-10">
          <span className="text-[9.5px] text-[#8E82AA] font-medium shrink-0">Try:</span>
          <button
            type="button"
            onClick={() => {
              const q = "Griha Pravesh ceremony";
              setMuhurtaQuery(q);
              handleCalculateMuhurta(q);
            }}
            className="px-2 py-0.5 rounded-full bg-white/10 hover:bg-white/15 text-[#E1DBEF] border border-white/15 transition-colors shrink-0"
          >
            🏡 Griha Pravesh
          </button>
          <button
            type="button"
            onClick={() => {
              const q = "Tech venture launch";
              setMuhurtaQuery(q);
              handleCalculateMuhurta(q);
            }}
            className="px-2 py-0.5 rounded-full bg-white/10 hover:bg-white/15 text-[#E1DBEF] border border-white/15 transition-colors shrink-0"
          >
            🚀 Tech Launch
          </button>
          <button
            type="button"
            onClick={() => {
              const q = "Buying new vehicle";
              setMuhurtaQuery(q);
              handleCalculateMuhurta(q);
            }}
            className="px-2 py-0.5 rounded-full bg-white/10 hover:bg-white/15 text-[#E1DBEF] border border-white/15 transition-colors shrink-0"
          >
            🚗 New Vehicle
          </button>
        </div>

        {/* Error message */}
        {muhurtaError && (
          <div className="p-3 rounded-2xl bg-rose-500/15 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{muhurtaError}</span>
          </div>
        )}

        {/* Computed Results Section (Formatted & Indented Cleanly) */}
        {muhurtaResult && muhurtaResult.slots && muhurtaResult.slots.length > 0 && (
          <div className="space-y-3.5 pt-2 border-t border-[#36194A] animate-in fade-in duration-300">
            {/* Location & Reset Bar */}
            <div className="flex items-center justify-between px-1">
              <span className="text-xs font-bold text-white flex items-center gap-1.5">
                <Sun className="w-4 h-4 text-[#E5A93C]" />
                <span>Recommended Auspicious Windows</span>
              </span>
              <div className="flex items-center gap-2">
                <span className="text-[10.5px] text-[#A299BC] truncate max-w-[120px]">
                  {muhurtaResult.location?.name?.split(",")[0]}
                </span>
                <button
                  onClick={() => {
                    setMuhurtaResult(null);
                    setMuhurtaQuery("");
                  }}
                  className="p-1 rounded-lg hover:bg-white/10 text-[#A299BC] hover:text-white transition-colors"
                  title="Clear results"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>

            {/* Slot Rank Selector */}
            <div className="grid grid-cols-3 gap-1.5 p-1 rounded-2xl bg-[#120720] border border-[#2B1444]">
              {muhurtaResult.slots.map((s, idx) => (
                <button
                  key={s.rank}
                  onClick={() => setSelectedSlotIndex(idx)}
                  className={`py-2 px-2 rounded-xl text-center transition-all ${
                    selectedSlotIndex === idx
                      ? "bg-gradient-to-r from-[#931B58] to-[#B21E68] text-white shadow-md font-bold"
                      : "text-[#A299BC] hover:text-white text-xs"
                  }`}
                >
                  <div className="text-[10px] uppercase font-bold tracking-wider">
                    Rank #{s.rank}
                  </div>
                  <div className="text-xs font-black text-[#FDE68A]">
                    {s.score} pts
                  </div>
                </button>
              ))}
            </div>

            {/* Active Slot Detailed Breakdown */}
            {(() => {
              const slot = muhurtaResult.slots[selectedSlotIndex] || muhurtaResult.slots[0];
              const startDt = new Date(slot.start_time_local);
              const endDt = new Date(slot.end_time_local);
              const dateStr = startDt.toLocaleDateString(undefined, {
                weekday: "long",
                month: "short",
                day: "numeric",
                year: "numeric",
              });
              const timeStr = `${startDt.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })} - ${endDt.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}`;

              return (
                <div className="p-4 rounded-2xl bg-[#150A26] border border-[#522064] space-y-3.5 shadow-lg">
                  {/* Status & Harmony Score */}
                  <div className="flex items-center justify-between">
                    <span className="px-2.5 py-0.5 rounded-full bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 text-[10.5px] font-bold flex items-center gap-1.5">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>Shubh Muhurta</span>
                    </span>
                    <div className="text-right">
                      <span className="text-[9.5px] text-[#A299BC] block font-medium">Harmony Score</span>
                      <strong className="text-base font-black text-[#FDE68A]">{slot.score} / 30</strong>
                    </div>
                  </div>

                  {/* Date & Time Window */}
                  <div className="p-3 rounded-xl bg-gradient-to-r from-[#220D32] to-[#2B103E] border border-[#481E60] space-y-1">
                    <div className="flex items-center gap-2 text-xs font-bold text-white">
                      <Calendar className="w-3.5 h-3.5 text-[#E5A93C]" />
                      <span>{dateStr}</span>
                    </div>
                    <div className="flex items-center gap-2 text-sm font-black text-[#FDE68A] font-mono">
                      <Clock className="w-3.5 h-3.5 text-[#F4B8DC]" />
                      <span>{timeStr}</span>
                      <span className="text-[10px] font-normal text-[#A299BC] ml-auto">Local Time</span>
                    </div>
                  </div>

                  {/* 5 Pillars of Vedic Panchanga (Indented Grid) */}
                  <div className="space-y-1.5">
                    <span className="text-[10px] uppercase font-bold text-[#A299BC] tracking-wider block">
                      5 Pillars of Panchanga
                    </span>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div className="p-2.5 rounded-xl bg-[#1A0C30] border border-[#34164C]">
                        <span className="text-[9.5px] text-[#8E82AA] block">Tithi</span>
                        <strong className="text-white block mt-0.5 truncate">{slot.panchanga.tithi}</strong>
                      </div>
                      <div className="p-2.5 rounded-xl bg-[#1A0C30] border border-[#34164C]">
                        <span className="text-[9.5px] text-[#8E82AA] block">Nakshatra</span>
                        <strong className="text-white block mt-0.5 truncate">{slot.panchanga.nakshatra}</strong>
                      </div>
                      <div className="p-2.5 rounded-xl bg-[#1A0C30] border border-[#34164C]">
                        <span className="text-[9.5px] text-[#8E82AA] block">Yoga & Karana</span>
                        <strong className="text-white block mt-0.5 truncate">
                          {slot.panchanga.yoga} • {slot.panchanga.karana}
                        </strong>
                      </div>
                      <div className="p-2.5 rounded-xl bg-[#1A0C30] border border-[#34164C]">
                        <span className="text-[9.5px] text-[#8E82AA] block">Choghadiya</span>
                        <strong className="text-[#FDE68A] block mt-0.5 font-bold flex items-center gap-1">
                          <span>✨ {slot.panchanga.choghadiya}</span>
                          {slot.panchanga.is_abhijit && (
                            <span className="text-[9px] px-1.5 py-0.2 rounded bg-amber-500/20 text-amber-300 ml-1">
                              Abhijit
                            </span>
                          )}
                        </strong>
                      </div>
                    </div>
                  </div>

                  {/* Personal Alignment: Tara Bala & Chandra Bala */}
                  <div className="p-3 rounded-xl bg-[#190C2E] border border-[#3C1952] space-y-1.5">
                    <div className="flex items-center justify-between text-xs font-bold text-white">
                      <span className="flex items-center gap-1.5">
                        <Sparkles className="w-3.5 h-3.5 text-[#E5A93C]" />
                        <span>Personal Alignment</span>
                      </span>
                      <span className="text-[10px] font-mono text-emerald-400">
                        {slot.personal_alignment.score_contribution}
                      </span>
                    </div>

                    <div className="space-y-1 text-xs text-[#DDD5EE]">
                      <div className="flex items-start justify-between gap-2">
                        <span className="text-[#A299BC] text-[11px]">Tara Bala:</span>
                        <strong className="text-white text-right text-[11px]">
                          {slot.personal_alignment.tara_bala}
                        </strong>
                      </div>
                      <div className="flex items-start justify-between gap-2">
                        <span className="text-[#A299BC] text-[11px]">Chandra Bala:</span>
                        <strong className="text-white text-right text-[11px]">
                          {slot.personal_alignment.chandra_bala}
                        </strong>
                      </div>
                    </div>
                  </div>

                  {/* Rationale / Vedic Explanation */}
                  <div className="p-3 rounded-xl bg-[#130722] border border-[#2F1444] text-xs text-[#DDD5EE] leading-relaxed">
                    <p>{slot.explanation}</p>
                  </div>

                  {/* 1-Tap Calendar Booking Actions */}
                  <div className="space-y-2 pt-1">
                    <a
                      href={slot.calendar_payload.google_calendar_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="w-full py-2.5 px-3 rounded-xl bg-gradient-to-r from-[#931B58] via-[#B21E68] to-[#E5A93C] text-white text-xs font-bold shadow-md hover:brightness-110 active:scale-95 transition-all flex items-center justify-center gap-2"
                    >
                      <Calendar className="w-3.5 h-3.5 text-white" />
                      <span>Add to Google Calendar (1-Click)</span>
                      <ExternalLink className="w-3 h-3 opacity-80" />
                    </a>

                    <div className="grid grid-cols-2 gap-2">
                      <button
                        type="button"
                        onClick={() => handleDownloadIcs(muhurtaResult.muhurta_id, slot.rank)}
                        className="py-2 px-2.5 rounded-xl bg-[#210D34] hover:bg-[#2E1546] border border-[#441C5A] text-white text-[11px] font-semibold flex items-center justify-center gap-1.5 transition-all active:scale-95"
                      >
                        <Download className="w-3 h-3 text-[#F4B8DC]" />
                        <span>Apple / Outlook (.ics)</span>
                      </button>

                      <button
                        type="button"
                        onClick={() => handleScheduleAlert(muhurtaResult.muhurta_id)}
                        className="py-2 px-2.5 rounded-xl bg-[#210D34] hover:bg-[#2E1546] border border-[#441C5A] text-white text-[11px] font-semibold flex items-center justify-center gap-1.5 transition-all active:scale-95"
                      >
                        <Bell className="w-3 h-3 text-[#FDE68A]" />
                        <span>{alertSuccess ? "Alerts Set!" : "24h & 1h Alerts"}</span>
                      </button>
                    </div>
                  </div>
                </div>
              );
            })()}

            {/* Advisory Note */}
            {muhurtaResult.advisory_note && (
              <div className="p-3 rounded-xl bg-[#140822] border border-[#381B4E] text-xs text-[#A299BC] space-y-1">
                <span className="text-[10px] font-bold text-[#E5A93C] uppercase tracking-wider block">
                  Vedic Remedial Advisory
                </span>
                <p className="leading-relaxed text-[#DDD5EE]">{muhurtaResult.advisory_note}</p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Daily Streak & Rewards Shortcut Banner */}
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

      {/* Standout Feature: Dasha Twin Milestone Card */}
      <DashaTwinCard
        userId={profile?.user_id || user?.id || "default_user"}
        lang={lang}
        onAskQuestion={(prompt) => {
          if (onSelectQuestion) onSelectQuestion(prompt);
          else if (onGoToAsk) onGoToAsk();
        }}
      />

      {/* Suggested Questions Section */}
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
