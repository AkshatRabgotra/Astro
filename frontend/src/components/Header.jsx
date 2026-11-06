import React, { useState, useRef, useEffect } from "react";
import { Sparkles, Edit2, Plus, Languages, ChevronDown, Check, UserPlus } from "lucide-react";
import { t } from "../i18n";

export default function Header({
  user,
  profile,
  profiles = [],
  balance,
  lang,
  setLang,
  onOpenPaywall,
  onEditProfile,
  onAddMember,
  onSelectProfile,
}) {
  const [showMemberDropdown, setShowMemberDropdown] = useState(false);
  const dropdownRef = useRef(null);

  const isZero = balance <= 0;

  const toggleLang = () => {
    setLang(lang === "en" ? "hi" : "en");
  };

  // Close dropdown on outside click
  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setShowMemberDropdown(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const activeName = profile?.name || user?.name || "Akshat";
  const userInitials = activeName.slice(0, 2).toUpperCase();

  // Combine current profile into profiles array if not already present
  const memberList = profiles.length > 0
    ? profiles
    : profile
    ? [profile]
    : [{ id: "default", name: activeName }];

  return (
    <header className="sticky top-0 z-40 bg-gradient-to-b from-[#4A0A28] via-[#35071D] to-[#120820]/95 backdrop-blur-xl border-b border-[#5E1238]/60 px-3 py-2.5 shadow-lg shadow-black/50">
      <div className="max-w-md mx-auto flex items-center justify-between gap-2">
        {/* Left: Melooha Logo + Active Profile Pill with Dropdown */}
        <div className="flex items-center gap-1.5 relative" ref={dropdownRef}>
          {/* Official Melooha Logo Icon */}
          <div className="w-8 h-8 rounded-full overflow-hidden shrink-0 border border-[#B21E68]/60 shadow-md shadow-[#931B58]/40 bg-[#70033E] flex items-center justify-center p-0.5">
            <img
              src="/melooha-logo.png"
              alt="Melooha Logo"
              className="w-full h-full object-contain"
            />
          </div>

          {/* User Profile Pill with Switcher Dropdown Toggle */}
          <div className="flex items-center rounded-full bg-[#200A1A]/90 border border-[#7D1B4D]/60 hover:border-[#B21E68] transition-all">
            <button
              onClick={() => setShowMemberDropdown(!showMemberDropdown)}
              className="flex items-center gap-1.5 py-1 pl-2 pr-1.5 text-left group shrink-0"
              title="Switch family member profile"
            >
              <div className="w-5 h-5 rounded-full bg-gradient-to-tr from-[#931B58] to-[#D8227E] text-white flex items-center justify-center font-bold text-[9.5px]">
                {userInitials}
              </div>
              <span className="text-xs font-semibold text-white tracking-wide truncate max-w-[70px]">
                {activeName}
              </span>
              <ChevronDown className={`w-3 h-3 text-[#E5A93C] transition-transform ${showMemberDropdown ? "rotate-180" : ""}`} />
            </button>

            {/* Dedicated Edit Pencil for active member */}
            <button
              onClick={(e) => {
                e.stopPropagation();
                setShowMemberDropdown(false);
                onEditProfile?.(profile);
              }}
              className="p-1 pr-2 hover:text-white text-[#E5A93C] transition-colors"
              title={`Edit ${activeName}'s birth details`}
            >
              <Edit2 className="w-3 h-3" />
            </button>
          </div>

          {/* Add Member Profile (+) Button */}
          <button
            onClick={() => {
              setShowMemberDropdown(false);
              onAddMember?.();
            }}
            className="w-6 h-6 rounded-full bg-[#280E24]/80 border border-[#5E1238] hover:border-[#E5A93C] text-[#C5B9DF] hover:text-white flex items-center justify-center text-xs shrink-0 transition-colors"
            title="Add new member (e.g. Avantika)"
          >
            <Plus className="w-3 h-3" />
          </button>

          {/* Dropdown Menu for Family Members */}
          {showMemberDropdown && (
            <div className="absolute left-0 sm:left-4 top-full mt-2 w-64 rounded-2xl bg-[#160B26] border-2 border-[#7D1B4D] shadow-[0_20px_60px_rgba(0,0,0,0.98)] py-2 z-[100] animate-in fade-in slide-in-from-top-2 duration-150 divide-y divide-[#32133D] ring-1 ring-white/10">
              <div className="px-3.5 py-1.5 bg-[#160B26]">
                <span className="text-[10px] font-bold text-[#E5A93C] uppercase tracking-wider block">
                  Family & Member Charts
                </span>
              </div>

              {/* Members List */}
              <div className="py-1 max-h-52 overflow-y-auto custom-scrollbar bg-[#160B26]">
                {memberList.map((m) => {
                  const isActive = m.id === profile?.id || m.name === activeName;
                  return (
                    <button
                      key={m.id || m.name}
                      onClick={() => {
                        onSelectProfile?.(m);
                        setShowMemberDropdown(false);
                      }}
                      className={`w-full px-3.5 py-2.5 text-left flex items-center justify-between hover:bg-[#2B1238] transition-colors group ${
                        isActive ? "bg-[#250F32]" : "bg-[#160B26]"
                      }`}
                    >
                      <div className="flex items-center gap-2.5 min-w-0">
                        <div className="w-6 h-6 rounded-full bg-gradient-to-tr from-[#931B58] to-[#D8227E] text-white flex items-center justify-center font-bold text-[10px] shrink-0">
                          {m.name.slice(0, 2).toUpperCase()}
                        </div>
                        <div className="min-w-0 truncate">
                          <span className="text-xs font-semibold text-white block truncate">
                            {m.name}
                          </span>
                          {m.place_name && (
                            <span className="text-[10px] text-[#A299BC] block truncate">
                              {m.place_name.split(",")[0]}
                            </span>
                          )}
                        </div>
                      </div>
                      {isActive && <Check className="w-4 h-4 text-[#E5A93C] shrink-0" />}
                    </button>
                  );
                })}
              </div>

              {/* Add New Member Action inside dropdown */}
              <div className="pt-2 px-3 bg-[#160B26]">
                <button
                  onClick={() => {
                    setShowMemberDropdown(false);
                    onAddMember?.();
                  }}
                  className="w-full py-2 px-3 rounded-xl bg-[#260D33] hover:bg-[#38144A] border border-[#5E1A48] text-white text-xs font-semibold flex items-center justify-center gap-2 transition-colors shadow-sm"
                >
                  <UserPlus className="w-3.5 h-3.5 text-[#F4B8DC]" />
                  <span>+ Add New Member</span>
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Right side: Language Toggle + Question Balance Badge */}
        <div className="flex items-center gap-1.5 shrink-0">
          {/* Language Toggle */}
          <button
            onClick={toggleLang}
            className="px-2 py-1 rounded-full bg-[#230C22]/80 border border-[#7D1B4D]/60 hover:border-[#E5A93C] text-[11px] font-bold text-[#F4B8DC] transition-all flex items-center gap-1 active:scale-95"
            title="Switch Language"
          >
            <Languages className="w-3 h-3 text-[#E5A93C]" />
            <span>{lang === "en" ? "हिन्दी" : "EN"}</span>
          </button>

          {/* Balance Badge with Gold Coin / Glow */}
          <button
            onClick={onOpenPaywall}
            className={`flex items-center gap-1 py-1 px-2.5 rounded-full text-xs font-semibold transition-all active:scale-95 ${
              isZero
                ? "bg-[#2A1028] border border-[#B21E68] text-[#F4B8DC] cosmic-glow"
                : "bg-gradient-to-r from-[#2A141A] to-[#381622] border border-[#E5A93C]/50 text-amber-200 hover:border-[#E5A93C]"
            }`}
          >
            <span className="w-2.5 h-2.5 rounded-full gold-coin inline-block shrink-0" />
            <span className="text-[11px] font-semibold text-white">
              {balance} {balance === 1 ? t("questionLeft", lang) : t("questionsLeft", lang)}
            </span>
            <span className="text-[#FDE68A] text-xs font-bold ml-0.5">
              {isZero ? t("addFree", lang) : "+"}
            </span>
          </button>
        </div>
      </div>
    </header>
  );
}
