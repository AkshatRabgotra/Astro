import React from "react";
import { Home, Sparkles, History, BarChart3, Eye, Gift } from "lucide-react";
import { t } from "../i18n";

export default function BottomNav({ activeTab, setActiveTab, lang = "en" }) {
  const tabs = [
    { id: "home", label: t("home", lang), icon: Home },
    { id: "rewards", label: t("rewards", lang), icon: Gift },
    { id: "ask", label: t("ask", lang), icon: Sparkles, isCenter: true },
    { id: "history", label: t("history", lang), icon: History },
    { id: "metrics", label: t("metrics", lang), icon: BarChart3 },
  ];

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-40 bg-[#0E091D]/95 backdrop-blur-lg border-t border-[#261A42] py-2 px-6 nav-shadow">
      <div className="max-w-md mx-auto flex items-center justify-around relative">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;

          if (tab.isCenter) {
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className="relative -top-4 flex flex-col items-center group focus:outline-none"
              >
                <div
                  className={`w-14 h-14 rounded-full flex items-center justify-center transition-all duration-300 shadow-xl ${
                    isActive
                      ? "bg-gradient-to-tr from-[#931B58] via-[#B21E68] to-[#D8227E] text-white cosmic-glow scale-105"
                      : "bg-[#1C1438] border-2 border-[#B21E68]/70 text-[#F4B8DC] hover:scale-105"
                  }`}
                >
                  <Eye className="w-6 h-6 text-[#E5A93C]" />
                </div>
                <span className={`text-[11px] font-semibold mt-1 transition-colors ${isActive ? "text-[#F4B8DC]" : "text-[#8E82AA]"}`}>
                  {tab.label}
                </span>
              </button>
            );
          }

          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className="flex flex-col items-center py-1 px-3 text-center transition-colors focus:outline-none"
            >
              <Icon
                className={`w-5 h-5 transition-transform duration-200 ${
                  isActive ? "text-[#F4B8DC] scale-110" : "text-[#7B7096] hover:text-[#A299BC]"
                }`}
              />
              <span
                className={`text-[10px] mt-1 font-medium transition-colors ${
                  isActive ? "text-[#F4B8DC] font-semibold" : "text-[#7B7096]"
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
