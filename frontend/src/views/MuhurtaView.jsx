import React, { useState, useEffect } from "react";
import {
  Calendar,
  Sparkles,
  Clock,
  Compass,
  MapPin,
  CheckCircle2,
  AlertCircle,
  ExternalLink,
  Download,
  Bell,
  ArrowRight,
  Sun,
  Moon,
  ChevronDown,
  ChevronUp,
  Share2,
  RotateCcw,
} from "lucide-react";
import { t } from "../i18n";

const PRESET_QUERIES = [
  "Starting my new tech venture next week in Bengaluru",
  "Griha Pravesh ceremony in Austin next month",
  "Buying a new vehicle this Friday in Mumbai",
  "Signing international business contract next Tuesday",
  "Auspicious time for investing & trading in New Delhi",
];

export default function MuhurtaView({
  user,
  profile,
  chartFacts,
  lang = "en",
  onSelectQuestion,
}) {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [selectedSlotIndex, setSelectedSlotIndex] = useState(0);
  const [alertSuccess, setAlertSuccess] = useState(false);

  const handleReset = () => {
    setQuery("");
    setResult(null);
    setError(null);
    setSelectedSlotIndex(0);
    setAlertSuccess(false);
  };

  // Active member details
  const activeName = profile?.name || user?.name || "You";
  const moonPlanet = chartFacts?.planets?.find((p) => p.planet === "Moon");
  const janmaNakshatra = moonPlanet?.nakshatra?.name || "Ashwini";
  const janmaRashi = moonPlanet?.sign || "Aries";

  const handlePlanMuhurta = async (queryString) => {
    const qText = (queryString || query).trim();
    if (!qText) return;

    setLoading(true);
    setError(null);
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
      setResult(data);
      setSelectedSlotIndex(0);
    } catch (err) {
      setError(err.message || "Failed to calculate auspicious window.");
    } finally {
      setLoading(false);
    }
  };

  const handleScheduleAlert = async (muhurtaId) => {
    try {
      const res = await fetch(`/api/muhurta/${muhurtaId}/schedule-alert`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          channel: "push",
        }),
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
      {/* 1. Header Banner */}
      <div className="crystal-card p-4 space-y-2 relative overflow-hidden border border-[#E5A93C]/40 shadow-xl">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-[#931B58] via-[#B21E68] to-[#E5A93C] flex items-center justify-center text-white shadow-md">
              <Calendar className="w-4 h-4 text-[#FDE68A]" />
            </div>
            <div>
              <h2 className="font-serif text-lg font-bold text-white leading-tight">
                Auspicious Muhurta Planner
              </h2>
              <span className="text-[11px] text-[#A299BC] block mt-0.5">
                Discover ideal Vedic timings for ventures, ceremonies & travel
              </span>
            </div>
          </div>
          {activeName && (
            <span className="text-[10px] font-semibold text-[#E5A93C] bg-[#22103E] px-2.5 py-1 rounded-full border border-[#522572] shrink-0">
              {activeName} {janmaNakshatra ? `• ${janmaNakshatra}` : ""}
            </span>
          )}
        </div>
      </div>

      {/* 2. Natural Language Query Input */}
      <div className="crystal-card p-4 space-y-3">
        <label className="block text-xs font-semibold text-[#DDD5EE]">
          What life event or ceremony are you planning?
        </label>
        <div className="relative">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handlePlanMuhurta()}
            placeholder="e.g. Starting my new tech venture next week in Bengaluru..."
            className="w-full pl-3.5 pr-24 py-3 rounded-2xl bg-[#170C2A] border border-[#3E1F58] text-white placeholder-[#7C6E96] text-xs focus:outline-none focus:border-[#E5A93C] shadow-inner"
          />
          <button
            onClick={() => handlePlanMuhurta()}
            disabled={loading || !query.trim()}
            className="absolute right-1.5 top-1.5 bottom-1.5 px-3.5 rounded-xl bg-gradient-to-r from-[#931B58] via-[#B21E68] to-[#E5A93C] text-white text-xs font-bold hover:brightness-110 active:scale-95 disabled:opacity-50 transition-all flex items-center gap-1 shadow-md"
          >
            {loading ? (
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
            ) : (
              <>
                <span>Calculate</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </>
            )}
          </button>
        </div>

        {/* Quick Suggestion Pills */}
        <div className="space-y-1.5 pt-1">
          <span className="text-[10px] text-[#8E82AA] font-bold block uppercase tracking-wider">
            Popular Ceremonies & Ventures:
          </span>
          <div className="flex flex-wrap gap-1.5">
            {PRESET_QUERIES.map((preset, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => {
                  setQuery(preset);
                  handlePlanMuhurta(preset);
                }}
                className="text-[10.5px] px-2.5 py-1 rounded-xl bg-[#170C28] hover:bg-[#281340] border border-[#3A1B54] hover:border-[#E5A93C]/50 text-[#C9BFDE] hover:text-white transition-all text-left truncate max-w-full"
              >
                {preset}
              </button>
            ))}
          </div>
        </div>
      </div>

      {error && (
        <div className="p-3 rounded-2xl bg-rose-500/15 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* 3. Muhurta Calculation Results */}
      {result && result.slots && result.slots.length > 0 && (
        <div className="space-y-3 animate-in fade-in duration-300">
          <div className="flex items-center justify-between px-1">
            <span className="text-xs font-bold text-white flex items-center gap-1.5">
              <Sun className="w-4 h-4 text-[#E5A93C]" />
              <span>Recommended Auspicious Windows</span>
            </span>
            <button
              onClick={handleReset}
              className="px-2.5 py-1 rounded-xl bg-[#25103E] hover:bg-[#38185C] border border-[#50247A] text-[11px] text-[#DDD5EE] hover:text-white flex items-center gap-1.5 active:scale-95 transition-all shadow-sm"
              title="Reset current calculation (saved in History)"
            >
              <RotateCcw className="w-3 h-3 text-[#E5A93C]" />
              <span>{lang === "hi" ? "रीसेट" : "Reset"}</span>
            </button>
          </div>

          {/* Slot Tabs / Selector */}
          <div className="grid grid-cols-3 gap-1.5 p-1 rounded-2xl bg-[#140A24] border border-[#2E1848]">
            {result.slots.map((s, idx) => (
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

          {/* Active Slot Detailed Card */}
          {(() => {
            const slot = result.slots[selectedSlotIndex] || result.slots[0];
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
              <div className="crystal-card p-5 space-y-4 border border-[#B21E68]/60 shadow-[0_15px_40px_rgba(0,0,0,0.7)] relative overflow-hidden">
                {/* Top Badge: Rank & Certified Auspicious */}
                <div className="flex items-center justify-between">
                  <span className="px-3 py-1 rounded-full bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 text-[10.5px] font-bold flex items-center gap-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>Certified Auspicious (Shubh Muhurta)</span>
                  </span>
                  <div className="text-right">
                    <span className="text-[10px] text-[#A299BC] block font-medium">Harmony Score</span>
                    <strong className="text-lg font-black text-[#FDE68A]">{slot.score} / 30</strong>
                  </div>
                </div>

                {/* Date & Time Window */}
                <div className="p-3.5 rounded-2xl bg-gradient-to-r from-[#220D32] to-[#2B103E] border border-[#481E60] space-y-1">
                  <div className="flex items-center gap-2 text-xs font-bold text-white">
                    <Calendar className="w-4 h-4 text-[#E5A93C]" />
                    <span>{dateStr}</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm font-black text-[#FDE68A] font-mono">
                    <Clock className="w-4 h-4 text-[#F4B8DC]" />
                    <span>{timeStr}</span>
                    <span className="text-[10px] font-normal text-[#A299BC] ml-auto">Local Time</span>
                  </div>
                </div>

                {/* 5-Pillar Classical Panchanga Grid */}
                <div>
                  <span className="text-[10px] uppercase font-bold text-[#A299BC] tracking-wider block mb-2">
                    5 Pillars of Vedic Panchanga
                  </span>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div className="p-2.5 rounded-xl bg-[#140B28] border border-[#2B1748]">
                      <span className="text-[9.5px] text-[#8E82AA] block">Tithi</span>
                      <strong className="text-white block mt-0.5 truncate">{slot.panchanga.tithi}</strong>
                    </div>
                    <div className="p-2.5 rounded-xl bg-[#140B28] border border-[#2B1748]">
                      <span className="text-[9.5px] text-[#8E82AA] block">Nakshatra</span>
                      <strong className="text-white block mt-0.5 truncate">{slot.panchanga.nakshatra}</strong>
                    </div>
                    <div className="p-2.5 rounded-xl bg-[#140B28] border border-[#2B1748]">
                      <span className="text-[9.5px] text-[#8E82AA] block">Yoga & Karana</span>
                      <strong className="text-white block mt-0.5 truncate">
                        {slot.panchanga.yoga} • {slot.panchanga.karana}
                      </strong>
                    </div>
                    <div className="p-2.5 rounded-xl bg-[#140B28] border border-[#2B1748]">
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
                <div className="p-3 rounded-2xl bg-[#180A2A] border border-[#3E1C58] space-y-2">
                  <div className="flex items-center justify-between text-xs font-bold text-white">
                    <span className="flex items-center gap-1.5">
                      <Sparkles className="w-3.5 h-3.5 text-[#E5A93C]" />
                      <span>Melooha Personal Alignment</span>
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

                {/* Grounded Vedic Explanation */}
                <div className="p-3.5 rounded-2xl bg-[#150B24] border border-[#2C1844] text-xs text-[#DDD5EE] leading-relaxed">
                  <p>{slot.explanation}</p>
                </div>

                {/* 1-Tap Calendar Booking Actions */}
                <div className="space-y-2 pt-1">
                  <a
                    href={slot.calendar_payload.google_calendar_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="w-full py-3 px-4 rounded-2xl bg-gradient-to-r from-[#931B58] via-[#B21E68] to-[#E5A93C] text-white text-xs font-bold shadow-lg shadow-[#B21E68]/30 hover:brightness-110 active:scale-95 transition-all flex items-center justify-center gap-2"
                  >
                    <Calendar className="w-4 h-4 text-white" />
                    <span>Add to Google Calendar (1-Click)</span>
                    <ExternalLink className="w-3.5 h-3.5 opacity-80" />
                  </a>

                  <div className="grid grid-cols-2 gap-2">
                    <button
                      type="button"
                      onClick={() => handleDownloadIcs(result.muhurta_id, slot.rank)}
                      className="py-2.5 px-3 rounded-xl bg-[#200F36] hover:bg-[#2E154C] border border-[#3E1F5C] text-white text-xs font-semibold flex items-center justify-center gap-1.5 transition-all active:scale-95"
                    >
                      <Download className="w-3.5 h-3.5 text-[#F4B8DC]" />
                      <span>Apple / Outlook (.ics)</span>
                    </button>

                    <button
                      type="button"
                      onClick={() => handleScheduleAlert(result.muhurta_id)}
                      className="py-2.5 px-3 rounded-xl bg-[#200F36] hover:bg-[#2E154C] border border-[#3E1F5C] text-white text-xs font-semibold flex items-center justify-center gap-1.5 transition-all active:scale-95"
                    >
                      <Bell className="w-3.5 h-3.5 text-[#FDE68A]" />
                      <span>{alertSuccess ? "Alerts Set!" : "24h & 1h Alerts"}</span>
                    </button>
                  </div>
                </div>
              </div>
            );
          })()}

          {/* Advisory Note */}
          {result.advisory_note && (
            <div className="p-3.5 rounded-2xl bg-[#140822] border border-[#381B4E] text-xs text-[#A299BC] space-y-1">
              <span className="text-[10px] font-bold text-[#E5A93C] uppercase tracking-wider block">
                Vedic Remedial Advisory
              </span>
              <p className="leading-relaxed text-[#DDD5EE]">{result.advisory_note}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
