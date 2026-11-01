import React, { useState, useEffect } from "react";
import Header from "./components/Header";
import BottomNav from "./components/BottomNav";
import OnboardingModal from "./components/OnboardingModal";
import PaywallModal from "./components/PaywallModal";
import EvidenceModal from "./components/EvidenceModal";

import HomeView from "./views/HomeView";
import AskView from "./views/AskView";
import HistoryView from "./views/HistoryView";
import MetricsView from "./views/MetricsView";
import RewardsView from "./views/RewardsView";

export default function App() {
  const [user, setUser] = useState(null);
  const [profile, setProfile] = useState(null);
  const [chartFacts, setChartFacts] = useState(null);
  const [balance, setBalance] = useState(1);
  const [activeTab, setActiveTab] = useState("home");
  const [selectedFact, setSelectedFact] = useState(null);
  const [showPaywall, setShowPaywall] = useState(false);
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [selectedQuestionPrompt, setSelectedQuestionPrompt] = useState("");
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [lang, setLang] = useState("en");

  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);
    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);
    return () => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
    };
  }, []);

  // Restore user from localStorage or show Onboarding on first launch
  useEffect(() => {
    const savedUserData = localStorage.getItem("melooha_user_data");
    if (savedUserData) {
      try {
        const parsed = JSON.parse(savedUserData);
        setUser(parsed.user);
        setProfile(parsed.profile);
        setChartFacts(parsed.chart_facts);
        setBalance(parsed.balance || 1);
        refreshBalance(parsed.user.id);
      } catch (e) {
        setShowOnboarding(true);
      }
    } else {
      setShowOnboarding(true);
    }
  }, []);

  const refreshBalance = async (userId) => {
    try {
      const res = await fetch(`/api/user/${userId}/balance`);
      if (res.ok) {
        const data = await res.json();
        setBalance(data.balance);
      }
    } catch (_) {}
  };

  const handleOnboardSuccess = (data) => {
    setUser(data.user);
    setProfile(data.profile);
    setChartFacts(data.chart_facts);
    setBalance(data.balance);
    localStorage.setItem("melooha_user_data", JSON.stringify(data));
    setShowOnboarding(false);
  };

  const handleTopupSuccess = (newBalance) => {
    setBalance(newBalance);
    setShowPaywall(false);
  };

  const handleSelectQuestionFromHome = (questionText) => {
    setSelectedQuestionPrompt(questionText);
    setActiveTab("ask");
  };

  return (
    <div className="min-h-screen bg-[#080511] text-[#E8E3F5] flex flex-col font-sans">
      {/* Offline Status Banner */}
      {!isOnline && (
        <div className="bg-amber-600/90 text-white text-xs py-1.5 px-4 text-center font-medium sticky top-0 z-50">
          You are currently offline. Cached readings and chart facts remain accessible.
        </div>
      )}

      {/* Header */}
      <Header
        user={user}
        balance={balance}
        lang={lang}
        setLang={setLang}
        onOpenPaywall={() => setShowPaywall(true)}
        onOpenOnboarding={() => setShowOnboarding(true)}
      />

      {/* Main View Area */}
      <main className="flex-1 overflow-x-hidden">
        {activeTab === "home" && (
          <HomeView
            chartFacts={chartFacts}
            profile={profile}
            lang={lang}
            onSelectQuestion={handleSelectQuestionFromHome}
            onGoToAsk={() => setActiveTab("ask")}
            onGoToRewards={() => setActiveTab("rewards")}
          />
        )}

        {activeTab === "rewards" && (
          <RewardsView
            user={user}
            balance={balance}
            lang={lang}
            onRefreshBalance={() => user && refreshBalance(user.id)}
            onOpenPaywall={() => setShowPaywall(true)}
          />
        )}

        {activeTab === "ask" && (
          <AskView
            user={user}
            profile={profile}
            chartFacts={chartFacts}
            balance={balance}
            lang={lang}
            onOpenPaywall={() => setShowPaywall(true)}
            onOpenEvidence={(fact) => setSelectedFact(fact)}
            initialQuestion={selectedQuestionPrompt}
            onQuestionCompleted={() => user && refreshBalance(user.id)}
          />
        )}

        {activeTab === "history" && (
          <HistoryView
            user={user}
            lang={lang}
            onOpenEvidence={(fact) => setSelectedFact(fact)}
          />
        )}

        {activeTab === "metrics" && <MetricsView lang={lang} />}
      </main>

      {/* Bottom Navigation */}
      <BottomNav activeTab={activeTab} setActiveTab={setActiveTab} lang={lang} />

      {/* Modals */}
      {showOnboarding && (
        <OnboardingModal onOnboardSuccess={handleOnboardSuccess} lang={lang} />
      )}

      {showPaywall && (
        <PaywallModal
          user={user}
          lang={lang}
          onTopupSuccess={handleTopupSuccess}
          onClose={() => setShowPaywall(false)}
        />
      )}

      {selectedFact && (
        <EvidenceModal
          fact={selectedFact}
          lang={lang}
          onClose={() => setSelectedFact(null)}
        />
      )}
    </div>
  );
}
