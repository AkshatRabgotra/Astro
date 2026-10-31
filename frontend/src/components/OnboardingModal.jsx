import React, { useState } from "react";
import { Sparkles, Compass, MapPin, Clock, Calendar, Check, AlertCircle } from "lucide-react";

const PRESET_PLACES = [
  { name: "Mumbai, India", lat: 19.0760, lon: 72.8777, tz: "Asia/Kolkata" },
  { name: "New Delhi, India", lat: 28.6139, lon: 77.2090, tz: "Asia/Kolkata" },
  { name: "Bengaluru, India", lat: 12.9716, lon: 77.5946, tz: "Asia/Kolkata" },
  { name: "New York, USA", lat: 40.7128, lon: -74.0060, tz: "America/New_York" },
  { name: "London, UK", lat: 51.5074, lon: -0.1278, tz: "Europe/London" },
];

export default function OnboardingModal({ onOnboardSuccess }) {
  const [name, setName] = useState("Akshat");
  const [birthDate, setBirthDate] = useState("1995-05-24");
  const [birthTime, setBirthTime] = useState("14:15");
  const [timeKnown, setTimeKnown] = useState(true);
  const [selectedPlace, setSelectedPlace] = useState(PRESET_PLACES[0]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!name.trim() || !birthDate) {
      setError("Please enter your name and date of birth.");
      return;
    }

    setLoading(true);
    setError(null);

    const payload = {
      name: name.trim(),
      birth_date: birthDate,
      birth_time: timeKnown ? (birthTime ? `${birthTime}:00` : null) : null,
      time_known: timeKnown,
      latitude: selectedPlace.lat,
      longitude: selectedPlace.lon,
      timezone_str: selectedPlace.tz,
      place_name: selectedPlace.name,
    };

    try {
      const res = await fetch("/api/onboarding", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Onboarding failed");
      }

      const data = await res.json();
      onOnboardSuccess(data);
    } catch (err) {
      setError(err.message || "Failed to calculate birth chart. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/85 backdrop-blur-md p-4">
      <div className="w-full max-w-md bg-[#130E26] border border-[#B21E68]/50 rounded-3xl p-6 sm:p-8 shadow-2xl relative animate-in zoom-in-95 duration-200 max-h-[95vh] overflow-y-auto">
        {/* Header */}
        <div className="text-center mb-6">
          <div className="inline-flex p-3 rounded-2xl bg-gradient-to-tr from-[#931B58] to-[#B21E68] text-white shadow-lg shadow-[#B21E68]/30 mb-2">
            <Compass className="w-7 h-7 text-[#E5A93C]" />
          </div>
          <h2 className="font-serif text-2xl font-bold text-white">
            Welcome to Melooha
          </h2>
          <p className="text-xs text-[#A299BC] mt-1">
            Enter your birth details to generate your grounded Vedic birth chart.
          </p>
        </div>

        {error && (
          <div className="mb-4 p-3 rounded-xl bg-rose-500/15 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Name */}
          <div>
            <label className="block text-xs font-medium text-[#C8BFDE] mb-1">
              Your Name
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Akshat"
              required
              className="w-full px-4 py-2.5 rounded-xl bg-[#1D1438] border border-[#3A275E] text-white placeholder-[#786994] focus:outline-none focus:border-[#B21E68] text-sm"
            />
          </div>

          {/* Birth Date */}
          <div>
            <label className="block text-xs font-medium text-[#C8BFDE] mb-1 flex items-center gap-1.5">
              <Calendar className="w-3.5 h-3.5 text-[#F4B8DC]" />
              Date of Birth
            </label>
            <input
              type="date"
              value={birthDate}
              onChange={(e) => setBirthDate(e.target.value)}
              required
              className="w-full px-4 py-2.5 rounded-xl bg-[#1D1438] border border-[#3A275E] text-white focus:outline-none focus:border-[#B21E68] text-sm"
            />
          </div>

          {/* Birth Time & "I don't know my time" toggle */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="text-xs font-medium text-[#C8BFDE] flex items-center gap-1.5">
                <Clock className="w-3.5 h-3.5 text-[#E5A93C]" />
                Time of Birth
              </label>
              <button
                type="button"
                onClick={() => setTimeKnown(!timeKnown)}
                className="text-xs text-[#F4B8DC] hover:underline flex items-center gap-1 font-medium"
              >
                {timeKnown ? "I don't know my time" : "I know my exact time"}
              </button>
            </div>

            {timeKnown ? (
              <input
                type="time"
                value={birthTime}
                onChange={(e) => setBirthTime(e.target.value)}
                className="w-full px-4 py-2.5 rounded-xl bg-[#1D1438] border border-[#3A275E] text-white focus:outline-none focus:border-[#B21E68] text-sm"
              />
            ) : (
              <div className="p-3 rounded-xl bg-[#1A1230] border border-[#3B295A] text-xs text-[#A299BC] leading-relaxed">
                <span className="text-[#E5A93C] font-semibold block mb-0.5">Time-dependent facts reserved</span>
                We'll compute your planet signs and dasha based on solar noon. House numbers and exact Lagna will be marked unavailable without guessing.
              </div>
            )}
          </div>

          {/* Place of Birth */}
          <div>
            <label className="block text-xs font-medium text-[#C8BFDE] mb-1 flex items-center gap-1.5">
              <MapPin className="w-3.5 h-3.5 text-[#B21E68]" />
              Place of Birth
            </label>
            <div className="grid grid-cols-2 gap-2 mb-2">
              {PRESET_PLACES.slice(0, 4).map((place) => (
                <button
                  type="button"
                  key={place.name}
                  onClick={() => setSelectedPlace(place)}
                  className={`p-2.5 rounded-xl text-xs font-medium text-left border transition-all truncate ${
                    selectedPlace.name === place.name
                      ? "bg-[#B21E68]/20 border-[#B21E68] text-white"
                      : "bg-[#1D1438] border-[#3A275E] text-[#9E93B8] hover:border-[#583E8C]"
                  }`}
                >
                  {place.name}
                </button>
              ))}
            </div>
            <p className="text-[11px] text-[#786B94]">
              Selected: <strong className="text-white">{selectedPlace.name}</strong> ({selectedPlace.tz})
            </p>
          </div>

          {/* Submit */}
          <button
            type="submit"
            disabled={loading}
            className="w-full mt-4 py-3.5 px-6 rounded-2xl font-semibold text-white bg-gradient-to-r from-[#931B58] via-[#B21E68] to-[#D8227E] hover:opacity-95 active:scale-[0.98] transition-all shadow-lg shadow-[#B21E68]/30 flex items-center justify-center gap-2"
          >
            {loading ? (
              <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
            ) : (
              <>
                <Sparkles className="w-4 h-4 text-[#E5A93C]" />
                <span>Calculate My Chart & Get 1 Free Question</span>
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
