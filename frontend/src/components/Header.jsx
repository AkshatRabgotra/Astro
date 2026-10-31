import React from "react";
import { Sparkles, Plus, CircleDot, ChevronRight, User } from "lucide-react";

export default function Header({ user, balance, onOpenPaywall, onOpenOnboarding }) {
  const isZero = balance <= 0;

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

        {/* Balance Badge */}
        <div className="flex items-center gap-2">
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
              {balance} {balance === 1 ? "Question" : "Questions"} left
            </span>
            <span className="text-[#F4B8DC] text-[11px] font-semibold ml-1 flex items-center">
              {isZero ? "Add +" : "Buy >"}
            </span>
          </button>
        </div>
      </div>
    </header>
  );
}
