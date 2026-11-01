import React from "react";
import { Sparkles, CircleDot, Languages } from "lucide-react";
import { t } from "../i18n";

export default function Header({ user, balance, lang, setLang, onOpenPaywall, onOpenOnboarding }) {
  const isZero = balance <= 0;

  const toggleLang = () => {
    setLang(lang === "en" ? "hi" : "en");
  };

  return (
    <header className="sticky top-0 z-40 bg-[#070311]/92 backdrop-blur-xl border-b border-[#2C1C4A] px-4 py-2.5 shadow-lg shadow-black/40">
      <div className="max-w-md mx-auto flex items-center justify-between">
        {/* User Profile Pill with Cosmic Aura */}
        <button
          onClick={onOpenOnboarding}
          className="flex items-center gap-2 p-1 pl-1 pr-3 rounded-full astro-badge hover:border-[#B21E68] transition-all text-left group"
        >
          <div className="relative">
            <div className="w-7 h-7 rounded-full bg-gradient-to-tr from-[#931B58] via-[#B21E68] to-[#D8227E] text-white flex items-center justify-center font-bold text-xs shadow-md shadow-[#B21E68]/40">
              {user ? user.name.slice(0, 2).toUpperCase() : "M"}
            </div>
            <span className="absolute -bottom-0.5 -right-0.5 w-2 h-2 rounded-full bg-emerald-400 border border-[#080511]" />
          </div>
          <div className="flex flex-col">
            <span className="text-xs font-bold text-white tracking-wide truncate max-w-[90px] group-hover:text-[#F4B8DC] transition-colors">
              {user ? user.name : "New User"}
            </span>
            <span className="text-[9.5px] text-[#A299BC] -mt-0.5 flex items-center gap-0.5">
              <span>Reading</span>
              <span className="text-[#E5A93C]">✦</span>
            </span>
          </div>
        </button>

        {/* Right side: Language Toggle + Crystal Balance Badge */}
        <div className="flex items-center gap-2">
          {/* Language Toggle */}
          <button
            onClick={toggleLang}
            className="px-2.5 py-1.5 rounded-full astro-badge hover:border-[#E5A93C] text-xs font-bold text-[#F4B8DC] transition-all flex items-center gap-1 active:scale-95"
            title="Switch Language"
          >
            <Languages className="w-3.5 h-3.5 text-[#E5A93C]" />
            <span className="text-[11px]">{lang === "en" ? "हिन्दी" : "EN"}</span>
          </button>

          {/* Balance Badge with Gold Coin / Glow */}
          <button
            onClick={onOpenPaywall}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold transition-all active:scale-95 ${
              isZero
                ? "bg-[#2A1028] border border-[#B21E68] text-[#F4B8DC] cosmic-glow"
                : "astro-badge-gold text-amber-200 hover:border-[#E5A93C]"
            }`}
          >
            <span className="w-3 h-3 rounded-full gold-coin inline-block shrink-0" />
            <span>
              {balance} {balance === 1 ? t("questionLeft", lang) : t("questionsLeft", lang)}
            </span>
            <span className="text-[#FDE68A] text-[11px] font-bold ml-0.5">
              {isZero ? t("addFree", lang) : "+"}
            </span>
          </button>
        </div>
      </div>
    </header>
  );
}
