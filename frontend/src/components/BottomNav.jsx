import React from "react";
import { Home, Compass, User, FileText, Eye } from "lucide-react";
import { t } from "../i18n";

export default function BottomNav({ activeTab, setActiveTab, lang = "en" }) {
  const tabs = [
    { id: "home", label: t("home", lang), icon: Home },
    { id: "reports", label: lang === "hi" ? "रिपोर्ट्स" : "Reports", icon: FileText },
    { id: "ask", label: t("ask", lang), isCenter: true },
    { id: "chart", label: t("chart", lang), icon: Compass },
    { id: "profile", label: t("profile", lang), icon: User },
  ];

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-40 bg-gradient-to-t from-[#080312] via-[#120822]/95 to-[#190C2E]/90 backdrop-blur-xl border-t border-[#4A1132]/60 py-1.5 px-4 nav-shadow">
      <div className="max-w-md mx-auto flex items-center justify-around relative">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;

          if (tab.isCenter) {
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className="relative -top-5 flex flex-col items-center group focus:outline-none"
              >
                <div
                  className={`w-14 h-14 rounded-full overflow-hidden flex items-center justify-center transition-all duration-300 ${
                    isActive
                      ? "ring-2 ring-white ring-offset-2 ring-offset-[#120822] scale-110 shadow-[0_0_30px_rgba(255,255,255,0.95),0_0_16px_rgba(216,34,126,0.85)]"
                      : "ring-2 ring-white/80 ring-offset-1 ring-offset-[#120822] hover:scale-105 shadow-[0_0_22px_rgba(255,255,255,0.7),0_0_12px_rgba(216,34,126,0.6)]"
                  }`}
                >
                  <img
                    src="/melooha-logo.png"
                    alt="Ask Melooha"
                    className="w-full h-full object-cover"
                  />
                </div>
                <span className={`text-[11px] font-bold mt-1 transition-colors ${isActive ? "text-white" : "text-[#DDD5EE]"}`}>
                  {tab.label}
                </span>
              </button>
            );
          }

          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex flex-col items-center py-1 px-3 text-center transition-all relative focus:outline-none rounded-xl ${
                isActive ? "bg-white/10 shadow-[0_0_14px_rgba(255,255,255,0.08)]" : ""
              }`}
            >
              <Icon
                className={`w-5 h-5 transition-transform duration-200 ${
                  isActive ? "text-white scale-105" : "text-[#887B9F] hover:text-[#C5B9DF]"
                }`}
              />
              <span
                className={`text-[10px] mt-0.5 font-medium transition-colors ${
                  isActive ? "text-white font-bold" : "text-[#887B9F]"
                }`}
              >
                {tab.label}
              </span>
            </button>
          );
        })}
      </div>
    </nav>
  );
}
