import React from "react";
import { Sparkles, Plus, CircleDot, ChevronRight, User, Languages } from "lucide-react";
import { t } from "../i18n";

export default function Header({ user, balance, lang, setLang, onOpenPaywall, onOpenOnboarding }) {
  const isZero = balance <= 0;

  const toggleLang = () => {
    setLang(lang === "en" ? "hi" : "en");
  };

  return (
    <header className="sticky top-0 z-40 bg-[#080511]/90 backdrop-blur-md border-b border-[#23173D] px-4 py-3">
      <div className="max-w-md mx-auto flex items-center justify-between">
        {/* User Profile Pill */}
        <button
          onClick={onOpenOnboarding}
          className="flex items-center gap-2 p-1.5 pr-3 rounded-full bg-[#18112C] border border-[#352554] hover:border-[#B21E68]/60 transition-all text-left"
        >
          <div className="w-7 h-7 rounded-full bg-gradient-to-tr from-[#931B58] to-[#B21E68] text-white flex items-center justify-center font-bold text-xs">
            {user ? user.name.slice(0, 2).toUpperCase() : "M"}
          </div>
          <span className="text-xs font-semibold text-white tracking-wide truncate max-w-[90px]">
            {user ? user.name : "New User"}
          </span>
        </button>

        {/* Right side: Language Toggle + Balance Badge */}
        <div className="flex items-center gap-2">
          {/* Language Toggle */}
          <button
            onClick={toggleLang}
            className="px-2.5 py-1.5 rounded-full bg-[#18112C] border border-[#352554] hover:border-[#B21E68] text-xs font-semibold text-[#F4B8DC] transition-all flex items-center gap-1"
            title="Switch Language"
          >
            <Languages className="w-3.5 h-3.5 text-[#E5A93C]" />
            <span>{lang === "en" ? "हिन्दी" : "EN"}</span>
          </button>

          {/* Balance Badge */}
          <button
            onClick={onOpenPaywall}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full border text-xs font-medium transition-all ${
              isZero
                ? "bg-[#2A1124] border-[#B21E68]/80 text-[#F4B8DC] shadow-md shadow-[#B21E68]/20"
                : "bg-[#18112C] border-[#3E2960] text-[#DED7EE] hover:border-[#B21E68]"
            }`}
          >
            <CircleDot className={`w-3.5 h-3.5 ${isZero ? "text-[#E5A93C] animate-pulse" : "text-[#B21E68]"}`} />
            <span>
              {balance} {balance === 1 ? t("questionLeft", lang) : t("questionsLeft", lang)}
            </span>
            <span className="text-[#F4B8DC] text-[11px] font-semibold ml-1 flex items-center">
              {isZero ? t("addFree", lang) : t("buyMore", lang) + " >"}
            </span>
          </button>
        </div>
      </div>
    </header>
  );
}
