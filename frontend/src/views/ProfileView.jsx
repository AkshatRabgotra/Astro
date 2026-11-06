import React, { useState } from "react";
import {
  User,
  Users,
  UserPlus,
  Shield,
  Gift,
  History,
  BarChart3,
  Languages,
  Sparkles,
  ChevronRight,
  Check,
  Palette,
  LogOut,
  Edit2,
  MapPin,
  Calendar,
  Clock,
} from "lucide-react";
import RewardsView from "./RewardsView";
import MetricsView from "./MetricsView";
import StyleGuideView from "./StyleGuideView";
import { t } from "../i18n";

export default function ProfileView({
  user,
  profile,
  profiles = [],
  chartFacts,
  balance,
  lang,
  setLang,
  onOpenPaywall,
  onGoToHistory,
  onEditProfile,
  onAddMember,
  onSelectProfile,
  onLogout,
}) {
  const [activeSubView, setActiveSubView] = useState(null); // null | "rewards" | "metrics" | "styleguide"

  if (activeSubView === "rewards") {
    return (
      <div className="space-y-4">
        <button
          onClick={() => setActiveSubView(null)}
          className="max-w-md mx-auto px-4 pt-3 flex items-center gap-1.5 text-xs text-[#E5A93C] hover:underline font-semibold"
        >
          <span>← {lang === "hi" ? "प्रोफ़ाइल पर वापस" : "Back to Profile"}</span>
        </button>
        <RewardsView user={user} balance={balance} lang={lang} onOpenPaywall={onOpenPaywall} />
      </div>
    );
  }

  if (activeSubView === "metrics") {
    return (
      <div className="space-y-4">
        <button
          onClick={() => setActiveSubView(null)}
          className="max-w-md mx-auto px-4 pt-3 flex items-center gap-1.5 text-xs text-[#E5A93C] hover:underline font-semibold"
        >
          <span>← {lang === "hi" ? "प्रोफ़ाइल पर वापस" : "Back to Profile"}</span>
        </button>
        <MetricsView />
      </div>
    );
  }

  if (activeSubView === "styleguide") {
    return <StyleGuideView onBack={() => setActiveSubView(null)} />;
  }

  // Active Member details (grounded to selected profile, NOT hardcoded to user)
  const activeName = profile?.name || user?.name || "Melooha Member";
  const activeInitials = activeName.slice(0, 2).toUpperCase();
  const activePlace = profile?.place_name || "Vedic Chart Active";

  const moonPlanet = chartFacts?.planets?.find((p) => p.planet === "Moon");
  const lagnaSign = chartFacts?.time_known
    ? chartFacts?.lagna_sign || chartFacts?.lagna?.sign || "Aries"
    : lang === "hi"
    ? "अनुपलब्ध"
    : "Unavailable";
  const moonSign = moonPlanet?.sign || "Moon";
  const nakshatraName = moonPlanet?.nakshatra?.name || "Nakshatra";

  // List of all family members in account
  const memberList =
    profiles.length > 0
      ? profiles
      : profile
      ? [profile]
      : [{ id: "default", name: activeName, place_name: activePlace }];

  return (
    <div className="space-y-4 pb-28 max-w-md mx-auto px-4 pt-3">
      {/* 1. Active Member Astrological Identity (Avantika / Akshat) */}
      <div className="crystal-card p-5 space-y-4 relative overflow-hidden border border-[#B21E68]/50 shadow-[0_10px_35px_rgba(0,0,0,0.6)]">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-3.5 min-w-0">
            {/* Glowing Avatar */}
            <div className="relative w-14 h-14 rounded-2xl bg-gradient-to-tr from-[#931B58] via-[#B21E68] to-[#E5A93C] p-0.5 shadow-xl shrink-0">
              <div className="w-full h-full rounded-[14px] bg-[#140827] flex items-center justify-center text-white font-serif font-bold text-xl">
                {activeInitials}
              </div>
            </div>

            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <h2 className="font-serif text-lg sm:text-xl font-bold text-white truncate">
                  {activeName}
                </h2>
                <span className="px-2 py-0.5 rounded-full bg-emerald-500/20 border border-emerald-500/40 text-[9px] font-bold text-emerald-300 uppercase tracking-wider shrink-0">
                  Active Member
                </span>
              </div>

              <p className="text-xs text-[#DDD5EE] truncate mt-0.5">
                {activePlace}
              </p>

              {profile?.birth_date && (
                <div className="flex items-center gap-2 text-[10.5px] text-[#A299BC] mt-1 font-mono">
                  <span>{profile.birth_date}</span>
                  {profile.birth_time && <span>• {profile.birth_time}</span>}
                </div>
              )}
            </div>
          </div>

          {onEditProfile && (
            <button
              onClick={() => onEditProfile(profile)}
              className="px-3 py-1.5 rounded-xl astro-badge text-xs font-semibold text-[#F4B8DC] hover:text-white transition-all flex items-center gap-1 shrink-0 active:scale-95"
              title="Edit this member's details"
            >
              <Edit2 className="w-3 h-3 text-[#E5A93C]" />
              <span>{lang === "hi" ? "संपादित करें" : "Edit"}</span>
            </button>
          )}
        </div>

        {/* 2. Astrological Core Chips (Lagna, Moon, Nakshatra) for Active Profile */}
        <div className="grid grid-cols-3 gap-2 pt-1 text-center">
          <div className="p-2.5 rounded-xl bg-[#140B28] border border-[#2B1A4B]">
            <span className="text-[10px] text-[#8E82AA] block">{t("ascendantLagna", lang)}</span>
            <strong className="text-xs text-white block mt-0.5 truncate">{lagnaSign}</strong>
          </div>
          <div className="p-2.5 rounded-xl bg-[#140B28] border border-[#2B1A4B]">
            <span className="text-[10px] text-[#8E82AA] block">Chandra Rashi</span>
            <strong className="text-xs text-white block mt-0.5 truncate">{moonSign}</strong>
          </div>
          <div className="p-2.5 rounded-xl bg-[#140B28] border border-[#2B1A4B]">
            <span className="text-[10px] text-[#8E82AA] block">Nakshatra</span>
            <strong className="text-xs text-white block mt-0.5 truncate">{nakshatraName}</strong>
          </div>
        </div>
      </div>

      {/* 3. Family Profiles & Kundalis Hub (Switch Member / Add Member) */}
      <div className="crystal-card p-4 space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-gradient-to-tr from-[#931B58] to-[#B21E68] text-white flex items-center justify-center shadow-md">
              <Users className="w-3.5 h-3.5 text-[#FDE68A]" />
            </div>
            <div>
              <h3 className="font-serif text-sm font-bold text-white">
                {lang === "hi" ? "पारिवारिक सदस्य एवं कुंडलियाँ" : "Family Members & Kundalis"}
              </h3>
              <p className="text-[10.5px] text-[#A299BC]">
                Each member has their own independent Vedic chart
              </p>
            </div>
          </div>

          <span className="text-[10.5px] font-mono px-2 py-0.5 rounded-full bg-[#201036] border border-[#3E2464] text-[#E5A93C]">
            {memberList.length} {memberList.length === 1 ? "Member" : "Members"}
          </span>
        </div>

        {/* Member Cards List */}
        <div className="space-y-2">
          {memberList.map((mem) => {
            const isActive = profile?.id === mem.id || (!profile?.id && mem.name === activeName);
            const initials = (mem.name || "M").slice(0, 2).toUpperCase();

            return (
              <div
                key={mem.id || mem.name}
                className={`p-3 rounded-2xl border transition-all flex items-center justify-between gap-3 ${
                  isActive
                    ? "bg-[#251034] border-[#B21E68] shadow-md shadow-[#931B58]/20"
                    : "bg-[#140C24] border-[#2E1A48] hover:border-[#4B2872]"
                }`}
              >
                <div
                  className="flex items-center gap-3 min-w-0 cursor-pointer flex-1"
                  onClick={() => onSelectProfile?.(mem)}
                >
                  <div
                    className={`w-9 h-9 rounded-xl flex items-center justify-center font-bold text-xs shrink-0 ${
                      isActive
                        ? "bg-gradient-to-tr from-[#931B58] to-[#E5A93C] text-white shadow-md"
                        : "bg-[#201438] text-[#DDD5EE] border border-[#38205E]"
                    }`}
                  >
                    {initials}
                  </div>

                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-white truncate">
                        {mem.name}
                      </span>
                      {isActive && (
                        <span className="px-1.5 py-0.2 rounded bg-emerald-500/20 text-emerald-300 text-[9px] font-bold border border-emerald-500/40">
                          Active
                        </span>
                      )}
                    </div>
                    <p className="text-[10.5px] text-[#A299BC] truncate">
                      {mem.place_name || mem.birth_date || "Birth details saved"}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-1.5 shrink-0">
                  {isActive ? (
                    <div className="w-7 h-7 rounded-lg bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 flex items-center justify-center">
                      <Check className="w-3.5 h-3.5" />
                    </div>
                  ) : (
                    <button
                      onClick={() => onSelectProfile?.(mem)}
                      className="px-2.5 py-1.5 rounded-xl bg-[#23123A] hover:bg-[#341854] text-xs font-semibold text-[#F4B8DC] transition-all"
                    >
                      Switch
                    </button>
                  )}

                  <button
                    onClick={() => onEditProfile?.(mem)}
                    className="p-1.5 rounded-lg bg-[#1B0F30] hover:bg-[#2B174B] text-[#A299BC] hover:text-white transition-colors"
                    title="Edit Details"
                  >
                    <Edit2 className="w-3 h-3 text-[#E5A93C]" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>

        {/* Add Member CTA */}
        {onAddMember && (
          <button
            onClick={onAddMember}
            className="w-full py-2.5 px-3 rounded-2xl bg-gradient-to-r from-[#2A1038] to-[#381648] hover:from-[#351545] hover:to-[#451B5A] border border-[#582064] text-white text-xs font-bold flex items-center justify-center gap-2 shadow-sm transition-all active:scale-98"
          >
            <UserPlus className="w-3.5 h-3.5 text-[#FDE68A]" />
            <span>+ Add Another Family Member</span>
          </button>
        )}
      </div>

      {/* 4. Single Balance Unit Card (Questions) - Shared under Account */}
      <div className="crystal-card-gold p-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full gold-coin flex items-center justify-center text-amber-950 font-bold shrink-0">
            🪙
          </div>
          <div>
            <span className="text-[10px] uppercase font-bold text-[#A299BC] tracking-wider block">
              {lang === "hi" ? "उपलब्ध प्रश्न शेष" : "Available Question Balance"}
            </span>
            <h3 className="font-serif text-lg font-bold text-white">
              {balance} {balance === 1 ? t("questionLeft", lang) : t("questionsLeft", lang)}
            </h3>
            <span className="text-[10px] text-[#DDD5EE] block">
              Shared across all family member profiles
            </span>
          </div>
        </div>

        <button
          onClick={onOpenPaywall}
          className="py-2 px-3.5 rounded-xl bg-gradient-to-r from-[#931B58] via-[#B21E68] to-[#E5A93C] text-white text-xs font-bold shadow-md hover:brightness-110 active:scale-95 transition-all"
        >
          {t("buyMore", lang)}
        </button>
      </div>

      {/* 5. Navigation Hub Links */}
      <div className="crystal-card p-2 space-y-1">
        {/* Rewards Hub Shortcut */}
        <button
          onClick={() => setActiveSubView("rewards")}
          className="w-full p-3 rounded-xl hover:bg-[#20133A] transition-colors flex items-center justify-between text-left group"
        >
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-[#251542] text-[#F4B8DC] flex items-center justify-center">
              <Gift className="w-4 h-4" />
            </div>
            <div>
              <h4 className="text-xs font-bold text-white">{t("rewards", lang)} & Daily Streaks</h4>
              <p className="text-[10.5px] text-[#A299BC]">Claim daily free questions & Japa Mala</p>
            </div>
          </div>
          <ChevronRight className="w-4 h-4 text-[#A299BC] group-hover:text-white" />
        </button>

        {/* History Shortcut */}
        <button
          onClick={onGoToHistory}
          className="w-full p-3 rounded-xl hover:bg-[#20133A] transition-colors flex items-center justify-between text-left group"
        >
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-[#251542] text-cyan-400 flex items-center justify-center">
              <History className="w-4 h-4" />
            </div>
            <div>
              <h4 className="text-xs font-bold text-white">{t("history", lang)}</h4>
              <p className="text-[10.5px] text-[#A299BC]">View your previous astrological readings</p>
            </div>
          </div>
          <ChevronRight className="w-4 h-4 text-[#A299BC] group-hover:text-white" />
        </button>

        {/* Language Selector */}
        <div className="w-full p-3 rounded-xl flex items-center justify-between text-left">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-[#251542] text-[#E5A93C] flex items-center justify-center">
              <Languages className="w-4 h-4" />
            </div>
            <div>
              <h4 className="text-xs font-bold text-white">App Language / भाषा</h4>
              <p className="text-[10.5px] text-[#A299BC]">Switch between English and हिन्दी</p>
            </div>
          </div>
          <div className="flex items-center gap-1 p-0.5 rounded-lg bg-[#140828] border border-[#2B1A4B]">
            <button
              onClick={() => setLang("en")}
              className={`px-2.5 py-1 rounded text-xs font-bold ${
                lang === "en" ? "bg-[#B21E68] text-white" : "text-[#A299BC]"
              }`}
            >
              EN
            </button>
            <button
              onClick={() => setLang("hi")}
              className={`px-2.5 py-1 rounded text-xs font-bold ${
                lang === "hi" ? "bg-[#B21E68] text-white" : "text-[#A299BC]"
              }`}
            >
              हिन्दी
            </button>
          </div>
        </div>
      </div>

      {/* 6. Admin & Challenge Evaluation Section (Displayed for Admin, not regular users) */}
      <div className="crystal-card p-4 space-y-3 border border-amber-500/35 relative overflow-hidden">
        <div className="flex items-center justify-between pb-2 border-b border-[#2C194D]">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
            <h3 className="font-serif text-xs font-bold text-white uppercase tracking-wider">
              Admin & Evaluation Console
            </h3>
          </div>
          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/20 text-[#FDE68A] border border-amber-500/40">
            For Admin Only
          </span>
        </div>

        <p className="text-[11px] text-[#A299BC] leading-relaxed">
          These telemetry instruments, conversion metrics, and design specifications are displayed exclusively for administrators and challenge reviewers, not for standard users.
        </p>

        <div className="space-y-2 pt-1">
          {/* Challenge Metrics & Retention Dashboard */}
          <button
            onClick={() => setActiveSubView("metrics")}
            className="w-full p-3 rounded-xl bg-[#170D2E]/90 hover:bg-[#251545] border border-[#3E2568] transition-all flex items-center justify-between text-left group active:scale-98 shadow-sm"
          >
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-[#271547] text-[#FDE68A] flex items-center justify-center shrink-0">
                <BarChart3 className="w-4 h-4" />
              </div>
              <div>
                <div className="flex items-center gap-1.5">
                  <h4 className="text-xs font-bold text-white">Challenge Metrics & Retention Funnel</h4>
                  <span className="text-[9px] px-1.5 py-0.2 rounded bg-amber-500/20 text-[#FDE68A] font-semibold">Admin</span>
                </div>
                <p className="text-[10.5px] text-[#A299BC]">2nd-question conversion, Dasha Twin virality, and RCT</p>
              </div>
            </div>
            <ChevronRight className="w-4 h-4 text-[#A299BC] group-hover:text-white shrink-0" />
          </button>

          {/* Design System & Living Style Guide */}
          <button
            onClick={() => setActiveSubView("styleguide")}
            className="w-full p-3 rounded-xl bg-[#170D2E]/90 hover:bg-[#251545] border border-[#3E2568] transition-all flex items-center justify-between text-left group active:scale-98 shadow-sm"
          >
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-[#271547] text-pink-400 flex items-center justify-center shrink-0">
                <Palette className="w-4 h-4" />
              </div>
              <div>
                <div className="flex items-center gap-1.5">
                  <h4 className="text-xs font-bold text-white">Design System & Living Style Guide</h4>
                  <span className="text-[9px] px-1.5 py-0.2 rounded bg-amber-500/20 text-[#FDE68A] font-semibold">Admin</span>
                </div>
                <p className="text-[10.5px] text-[#A299BC]">Documented design tokens, color ramps, typography, and states</p>
              </div>
            </div>
            <ChevronRight className="w-4 h-4 text-[#A299BC] group-hover:text-white shrink-0" />
          </button>
        </div>
      </div>

      {/* 6. Legal & Privacy Notice */}
      <div className="crystal-card p-4 text-xs text-[#A299BC] space-y-2">
        <div className="flex items-center gap-1.5 text-white font-bold">
          <Shield className="w-3.5 h-3.5 text-[#E5A93C]" />
          <span>Privacy & Data Honesty</span>
        </div>
        <p className="text-[11px] text-[#C5B9DF] leading-relaxed">
          Melooha uses Swiss Ephemeris for mathematical sidereal coordinates. All astrological interpretations are intended for self-reflection and personal empowerment.
        </p>
      </div>

      {/* Logout Action */}
      {onLogout && (
        <button
          onClick={onLogout}
          className="w-full p-3 rounded-2xl bg-[#1B0C24]/80 hover:bg-[#2E1235] border border-[#4A163B] text-rose-300 text-xs font-semibold flex items-center justify-center gap-2 transition-all active:scale-98 shadow-md"
        >
          <LogOut className="w-4 h-4 text-rose-400" />
          <span>{lang === "hi" ? "लॉग आउट करें" : "Sign Out / Switch Account"}</span>
        </button>
      )}

      {/* App Version */}
      <div className="text-center text-[10px] text-[#695D84] pt-2">
        Melooha Vedic Astrology • v1.2.0
      </div>
    </div>
  );
}
