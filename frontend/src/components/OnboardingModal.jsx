import React, { useState, useEffect, useRef } from "react";
import { Sparkles, Compass, MapPin, Clock, Calendar, Check, AlertCircle, Search, ChevronDown, ChevronUp, Globe } from "lucide-react";

const POPULAR_PRESETS = [
  { name: "Mumbai, Maharashtra, India", lat: 19.0760, lon: 72.8777, tz: "Asia/Kolkata", short: "Mumbai" },
  { name: "New Delhi, Delhi, India", lat: 28.6139, lon: 77.2090, tz: "Asia/Kolkata", short: "Delhi" },
  { name: "Bengaluru, Karnataka, India", lat: 12.9716, lon: 77.5946, tz: "Asia/Kolkata", short: "Bengaluru" },
  { name: "Pune, Maharashtra, India", lat: 18.5204, lon: 73.8567, tz: "Asia/Kolkata", short: "Pune" },
  { name: "London, UK", lat: 51.5074, lon: -0.1278, tz: "Europe/London", short: "London" },
  { name: "New York, USA", lat: 40.7128, lon: -74.0060, tz: "America/New_York", short: "New York" },
  { name: "Dubai, UAE", lat: 25.2048, lon: 55.2708, tz: "Asia/Dubai", short: "Dubai" },
];

export default function OnboardingModal({ onOnboardSuccess }) {
  const [name, setName] = useState("Akshat");
  const [birthDate, setBirthDate] = useState("1995-05-24");
  const [birthTime, setBirthTime] = useState("14:15");
  const [timeKnown, setTimeKnown] = useState(true);

  // Selected place object
  const [selectedPlace, setSelectedPlace] = useState(POPULAR_PRESETS[0]);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);

  // Manual coordinate overrides
  const [showManualCoords, setShowManualCoords] = useState(false);
  const [customLat, setCustomLat] = useState(19.0760);
  const [customLon, setCustomLon] = useState(72.8777);
  const [customTz, setCustomTz] = useState("Asia/Kolkata");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const dropdownRef = useRef(null);

  // Close dropdown on click outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setShowDropdown(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Debounced search for cities
  useEffect(() => {
    if (!searchQuery.trim()) {
      setSearchResults([]);
      return;
    }

    const timer = setTimeout(async () => {
      setIsSearching(true);
      try {
        const res = await fetch(`/api/places/search?q=${encodeURIComponent(searchQuery.trim())}&limit=12`);
        if (res.ok) {
          const data = await res.json();
          setSearchResults(data.places || []);
        }
      } catch (err) {
        console.error("City search error:", err);
      } finally {
        setIsSearching(false);
      }
    }, 200);

    return () => clearTimeout(timer);
  }, [searchQuery]);

  const handleSelectCity = (city) => {
    setSelectedPlace(city);
    setCustomLat(city.lat);
    setCustomLon(city.lon);
    setCustomTz(city.tz);
    setSearchQuery("");
    setShowDropdown(false);
  };

  const handleCustomPlaceApply = () => {
    if (!searchQuery.trim()) return;
    const customCity = {
      name: searchQuery.trim(),
      lat: customLat,
      lon: customLon,
      tz: customTz,
    };
    setSelectedPlace(customCity);
    setShowDropdown(false);
  };

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
      latitude: showManualCoords ? parseFloat(customLat) : selectedPlace.lat,
      longitude: showManualCoords ? parseFloat(customLon) : selectedPlace.lon,
      timezone_str: showManualCoords ? customTz : selectedPlace.tz,
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
      <div className="w-full max-w-lg bg-[#130E26] border border-[#B21E68]/50 rounded-3xl p-6 sm:p-8 shadow-2xl relative animate-in zoom-in-95 duration-200 max-h-[92vh] overflow-y-auto">
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

          {/* Place of Birth with Global Autocomplete Search */}
          <div className="relative" ref={dropdownRef}>
            <label className="block text-xs font-medium text-[#C8BFDE] mb-1 flex items-center justify-between">
              <span className="flex items-center gap-1.5">
                <MapPin className="w-3.5 h-3.5 text-[#B21E68]" />
                Place of Birth (Any City / Town Worldwide)
              </span>
              <button
                type="button"
                onClick={() => setShowManualCoords(!showManualCoords)}
                className="text-[11px] text-[#A299BC] hover:text-[#F4B8DC] flex items-center gap-0.5"
              >
                {showManualCoords ? "Hide manual coords" : "Manual coords"}
                {showManualCoords ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
              </button>
            </label>

            {/* Search Input Box */}
            <div className="relative">
              <Search className="w-4 h-4 text-[#786994] absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => {
                  setSearchQuery(e.target.value);
                  setShowDropdown(true);
                }}
                onFocus={() => setShowDropdown(true)}
                placeholder="Search any city or country (e.g. Pune, Patna, London, Dubai...)"
                className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-[#1D1438] border border-[#3A275E] text-white placeholder-[#786994] focus:outline-none focus:border-[#B21E68] text-sm"
              />
              {isSearching && (
                <div className="absolute right-3.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 border-2 border-[#B21E68] border-t-transparent rounded-full animate-spin" />
              )}
            </div>

            {/* Autocomplete Dropdown */}
            {showDropdown && (
              <div className="absolute left-0 right-0 top-full mt-1.5 bg-[#17102E] border border-[#443068] rounded-xl shadow-2xl z-30 max-h-56 overflow-y-auto divide-y divide-[#2A1E45]">
                {searchResults.length > 0 ? (
                  searchResults.map((city, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => handleSelectCity(city)}
                      className="w-full text-left px-3.5 py-2.5 hover:bg-[#2A1B4A] transition-colors flex items-center justify-between group"
                    >
                      <div>
                        <p className="text-xs font-semibold text-white group-hover:text-[#F4B8DC]">
                          {city.name}
                        </p>
                        <p className="text-[10px] text-[#867A9F]">
                          Lat: {city.lat.toFixed(2)}°, Lon: {city.lon.toFixed(2)}° • {city.tz}
                        </p>
                      </div>
                      <Check className="w-3.5 h-3.5 text-[#B21E68] opacity-0 group-hover:opacity-100 shrink-0" />
                    </button>
                  ))
                ) : searchQuery.trim().length > 1 ? (
                  <div className="p-3 text-center">
                    <p className="text-xs text-[#A299BC] mb-2">
                      No exact match for "{searchQuery}".
                    </p>
                    <button
                      type="button"
                      onClick={handleCustomPlaceApply}
                      className="px-3 py-1.5 rounded-lg bg-[#B21E68]/30 hover:bg-[#B21E68] text-white text-xs font-medium transition-all"
                    >
                      Use "{searchQuery}" as Place Name
                    </button>
                  </div>
                ) : (
                  <div className="p-3 text-xs text-[#867A9F] text-center">
                    Type 2+ letters to search from 100+ cities worldwide...
                  </div>
                )}
              </div>
            )}

            {/* Quick Popular City Pills */}
            <div className="mt-2.5 flex flex-wrap gap-1.5">
              <span className="text-[11px] text-[#786B94] self-center mr-1">Popular:</span>
              {POPULAR_PRESETS.map((place) => (
                <button
                  type="button"
                  key={place.short}
                  onClick={() => handleSelectCity(place)}
                  className={`px-2.5 py-1 rounded-lg text-xs font-medium border transition-all ${
                    selectedPlace.name === place.name
                      ? "bg-[#B21E68] border-[#B21E68] text-white shadow-sm"
                      : "bg-[#1D1438] border-[#3A275E] text-[#9E93B8] hover:border-[#583E8C] hover:text-white"
                  }`}
                >
                  {place.short}
                </button>
              ))}
            </div>

            {/* Currently Selected Location Pill */}
            <div className="mt-2 p-2.5 rounded-xl bg-[#181130] border border-[#352554] flex items-center justify-between text-xs">
              <div className="flex items-center gap-2 overflow-hidden">
                <Globe className="w-4 h-4 text-[#E5A93C] shrink-0" />
                <div className="truncate">
                  <span className="text-[#A299BC] block text-[10px]">Selected Birth Place</span>
                  <strong className="text-white truncate block">{selectedPlace.name}</strong>
                </div>
              </div>
              <div className="text-right text-[10px] text-[#867A9F] shrink-0 pl-2">
                <span>{selectedPlace.tz}</span>
              </div>
            </div>

            {/* Manual Lat/Lon/Tz Override (Collapsible) */}
            {showManualCoords && (
              <div className="mt-2.5 p-3 rounded-xl bg-[#160F2C] border border-[#443068] space-y-2 text-xs animate-in slide-in-from-top-2 duration-150">
                <div className="flex items-center justify-between text-[11px] text-[#E5A93C] font-semibold">
                  <span>Custom Exact Coordinates</span>
                  <span>Overrides location defaults</span>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="text-[10px] text-[#A299BC] block mb-0.5">Latitude (°N/S)</label>
                    <input
                      type="number"
                      step="any"
                      value={customLat}
                      onChange={(e) => setCustomLat(parseFloat(e.target.value) || 0)}
                      className="w-full px-2.5 py-1.5 rounded-lg bg-[#1E153A] border border-[#3A275E] text-white text-xs"
                    />
                  </div>
                  <div>
                    <label className="text-[10px] text-[#A299BC] block mb-0.5">Longitude (°E/W)</label>
                    <input
                      type="number"
                      step="any"
                      value={customLon}
                      onChange={(e) => setCustomLon(parseFloat(e.target.value) || 0)}
                      className="w-full px-2.5 py-1.5 rounded-lg bg-[#1E153A] border border-[#3A275E] text-white text-xs"
                    />
                  </div>
                </div>
                <div>
                  <label className="text-[10px] text-[#A299BC] block mb-0.5">IANA Timezone</label>
                  <input
                    type="text"
                    value={customTz}
                    onChange={(e) => setCustomTz(e.target.value)}
                    placeholder="e.g. Asia/Kolkata, America/New_York"
                    className="w-full px-2.5 py-1.5 rounded-lg bg-[#1E153A] border border-[#3A275E] text-white text-xs"
                  />
                </div>
              </div>
            )}
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
