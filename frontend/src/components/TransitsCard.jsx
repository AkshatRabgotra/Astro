import React, { useState, useEffect } from "react";
import { Compass, Sparkles, AlertCircle, Shield, ChevronRight, RefreshCw, Sun, Moon } from "lucide-react";

export default function TransitsCard({ profile, onSelectTransitQuestion }) {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!profile || !profile.id) return;

    fetch(`/api/chart/${profile.id}/transits`)
      .then((res) => {
        if (!res.ok) throw new Error("Failed to load transits");
        return res.json();
      })
      .then((data) => {
        setReport(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Transits load error:", err);
        setLoading(false);
      });
  }, [profile]);

  if (loading) {
    return (
      <div className="glass-panel p-5 text-center text-[#8E82AA] text-xs flex items-center justify-center gap-2">
        <div className="w-4 h-4 border-2 border-[#B21E68] border-t-transparent rounded-full animate-spin" />
        <span>Calculating live planetary transits (Gochara)...</span>
      </div>
    );
  }

  if (!report) {
    return null;
  }

  return (
    <div className="glass-panel p-4 sm:p-5 relative overflow-hidden space-y-3.5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-[#931B58] to-[#B21E68] text-white flex items-center justify-center shadow-md">
            <Compass className="w-4 h-4 text-[#E5A93C]" />
          </div>
          <div>
            <h3 className="font-serif text-sm sm:text-base font-bold text-white flex items-center gap-1.5">
              Live Planetary Transits (Gochara Today)
            </h3>
            <p className="text-[11px] text-[#A299BC]">
              Real-time positions in the sky relative to your natal Moon in {report.natal_moon_sign}
            </p>
          </div>
        </div>
      </div>

      {/* Sade Sati Status Card */}
      <div
        className={`p-3 rounded-2xl border flex items-start gap-2.5 ${
          report.sade_sati_active
            ? "bg-amber-950/30 border-amber-500/40 text-amber-200"
            : "bg-[#181131] border-[#372659] text-[#E0D8F0]"
        }`}
      >
        <Shield className={`w-4 h-4 mt-0.5 shrink-0 ${report.sade_sati_active ? "text-amber-400" : "text-[#E5A93C]"}`} />
        <div className="text-xs space-y-0.5">
          <strong className="block text-white font-semibold">
            {report.sade_sati_active ? "Sade Sati Active" : "No Sade Sati Active"}
          </strong>
          <p className="text-[11px] text-[#B5A8D3] leading-relaxed">
            {report.sade_sati_status}
          </p>
        </div>
      </div>

      {/* Jupiter & Saturn Highlights */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
        <div className="p-3 rounded-xl bg-[#17102D] border border-[#2D1F4D] space-y-1">
          <div className="flex items-center justify-between">
            <span className="text-[10px] uppercase font-bold text-[#E5A93C] tracking-wider">
              Jupiter (Guru)
            </span>
            <span className="text-[10px] text-[#7E7398]">Expansive</span>
          </div>
          <p className="text-[11px] text-[#DDD5EE] leading-relaxed">
            {report.jupiter_transit_summary}
          </p>
        </div>

        <div className="p-3 rounded-xl bg-[#17102D] border border-[#2D1F4D] space-y-1">
          <div className="flex items-center justify-between">
            <span className="text-[10px] uppercase font-bold text-[#60A5FA] tracking-wider">
              Saturn (Shani)
            </span>
            <span className="text-[10px] text-[#7E7398]">Karmic</span>
          </div>
          <p className="text-[11px] text-[#DDD5EE] leading-relaxed">
            {report.saturn_transit_summary}
          </p>
        </div>
      </div>

      {/* Mini Transit Chips Carousel */}
      <div>
        <span className="text-[10px] uppercase tracking-wider text-[#8A7EA6] font-semibold block mb-1.5">
          Planetary Positions in Sky Today
        </span>
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 scrollbar-none">
          {report.transits.map((tp) => (
            <div
              key={tp.planet}
              className="px-2.5 py-1.5 rounded-xl bg-[#1B1235] border border-[#352554] text-xs shrink-0 flex items-center gap-1.5"
            >
              <span className="font-bold text-white">{tp.planet}</span>
              <span className="text-[10px] text-[#E5A93C]">{tp.sign}</span>
              <span className="text-[9px] px-1 py-0.2 rounded bg-[#B21E68]/30 text-[#F4B8DC]">
                H{tp.house_from_moon}
              </span>
              {tp.is_retrograde && (
                <span className="text-[9px] text-amber-300 font-bold">®</span>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* 1-Tap Action */}
      {onSelectTransitQuestion && (
        <button
          onClick={() =>
            onSelectTransitQuestion(
              `How are today's planetary transits (especially Jupiter in House ${
                report.transits.find((p) => p.planet === "Jupiter")?.house_from_moon
              } and Saturn in House ${
                report.transits.find((p) => p.planet === "Saturn")?.house_from_moon
              }) impacting my career and personal growth right now?`
            )
          }
          className="w-full mt-1 py-2 px-3 rounded-xl bg-[#B21E68]/20 hover:bg-[#B21E68]/40 border border-[#B21E68]/50 text-xs font-semibold text-[#F4B8DC] flex items-center justify-center gap-1.5 transition-all active:scale-[0.98]"
        >
          <Sparkles className="w-3.5 h-3.5 text-[#E5A93C]" />
          <span>Ask how today's transits affect me</span>
          <ChevronRight className="w-3.5 h-3.5" />
        </button>
      )}
    </div>
  );
}
