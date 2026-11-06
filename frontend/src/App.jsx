import React, { useState, useEffect } from "react";
import { Sparkles } from "lucide-react";
import Header from "./components/Header";
import BottomNav from "./components/BottomNav";
import OnboardingModal from "./components/OnboardingModal";
import PaywallModal from "./components/PaywallModal";
import EvidenceModal from "./components/EvidenceModal";

import HomeView from "./views/HomeView";
import ReportsView from "./views/ReportsView";
import ChartView from "./views/ChartView";
import AskView from "./views/AskView";
import HistoryView from "./views/HistoryView";
import ProfileView from "./views/ProfileView";
import MetricsView from "./views/MetricsView";
import RewardsView from "./views/RewardsView";
import StyleGuideView from "./views/StyleGuideView";
import LoginView from "./views/LoginView";
import MuhurtaView from "./views/MuhurtaView";

export default function App() {
  const [user, setUser] = useState(null);
  const [profile, setProfile] = useState(null);
  const [profiles, setProfiles] = useState([]);
  const [chartFacts, setChartFacts] = useState(null);
  const [balance, setBalance] = useState(1);
  const [activeTab, setActiveTab] = useState(() => {
    if (typeof window !== "undefined") {
      if (window.location.pathname === "/styleguide" || window.location.hash === "#styleguide") {
        return "styleguide";
      }
    }
    return "home";
  });
  const [selectedFact, setSelectedFact] = useState(null);
  const [showPaywall, setShowPaywall] = useState(false);
  const [onboardingConfig, setOnboardingConfig] = useState({
    show: false,
    mode: "edit", // "edit" | "add_member"
    targetProfile: null,
  });
  const [selectedQuestionPrompt, setSelectedQuestionPrompt] = useState("");
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [lang, setLang] = useState("en");

  // Background question generation tracker so user can navigate elsewhere without cancellation
  const [streamingInfo, setStreamingInfo] = useState({
    isStreaming: false,
    streamStatus: "",
    lastQuestion: "",
    hasUnreadAnswer: false,
  });

  const handleStreamingStateChange = ({ isStreaming, streamStatus, lastQuestion }) => {
    setStreamingInfo((prev) => {
      const wasStreaming = prev.isStreaming;
      const finishedNow = wasStreaming && !isStreaming;
      return {
        isStreaming,
        streamStatus,
        lastQuestion,
        hasUnreadAnswer: finishedNow ? activeTab !== "ask" : prev.hasUnreadAnswer,
      };
    });
  };

  useEffect(() => {
    if (activeTab === "ask" && streamingInfo.hasUnreadAnswer) {
      setStreamingInfo((prev) => ({ ...prev, hasUnreadAnswer: false }));
    }
  }, [activeTab]);

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

  // Restore user & family profiles from localStorage
  useEffect(() => {
    const savedUserData = localStorage.getItem("melooha_user_data");
    if (savedUserData) {
      try {
        const parsed = JSON.parse(savedUserData);
        setUser(parsed.user);
        setProfile(parsed.profile);
        setProfiles(parsed.profiles || (parsed.profile ? [parsed.profile] : []));
        setChartFacts(parsed.chart_facts);
        setBalance(parsed.balance || 1);
        if (parsed.user?.id) {
          refreshBalance(parsed.user.id);
          fetchProfiles(parsed.user.id);
        }
      } catch (e) {
        localStorage.removeItem("melooha_user_data");
      }
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

  const fetchProfiles = async (userId) => {
    try {
      const res = await fetch(`/api/user/${userId}/profiles`);
      if (res.ok) {
        const data = await res.json();
        if (data.profiles && data.profiles.length > 0) {
          setProfiles(data.profiles);
        }
      }
    } catch (_) {}
  };

  const handleSelectProfile = async (target) => {
    if (!target || !target.id) return;
    try {
      const res = await fetch(`/api/profile/${target.id}/chart`);
      if (res.ok) {
        const data = await res.json();
        setProfile(data.profile);
        setChartFacts(data.chart_facts);

        // Persist active profile selection
        const saved = localStorage.getItem("melooha_user_data");
        if (saved) {
          try {
            const parsed = JSON.parse(saved);
            parsed.profile = data.profile;
            parsed.chart_facts = data.chart_facts;
            localStorage.setItem("melooha_user_data", JSON.stringify(parsed));
          } catch (_) {}
        }
      }
    } catch (e) {
      console.error("Failed to load chart for profile:", e);
    }
  };

  const handleLoginSuccess = (data) => {
    setUser(data.user);
    const userProfiles = data.profiles || (data.profile ? [data.profile] : []);
    setProfiles(userProfiles);

    if (data.profile) {
      setProfile(data.profile);
      setChartFacts(data.chart_facts);
      setBalance(data.balance ?? 5);
      localStorage.setItem(
        "melooha_user_data",
        JSON.stringify({
          ...data,
          profiles: userProfiles,
        })
      );
      setOnboardingConfig({ show: false, mode: "edit", targetProfile: null });
    } else {
      // New Google / guest user without a birth profile yet
      setProfile(null);
      setChartFacts(null);
      setBalance(data.balance || 5);
      setOnboardingConfig({ show: true, mode: "add_member", targetProfile: null });
    }
  };

  const handleLogout = () => {
    setUser(null);
    setProfile(null);
    setProfiles([]);
    setChartFacts(null);
    setOnboardingConfig({ show: false, mode: "edit", targetProfile: null });
    localStorage.removeItem("melooha_user_data");
  };

  const handleOnboardSuccess = (data) => {
    const mergedUser = { ...(user || {}), ...(data.user || {}) };
    setUser(mergedUser);
    setProfile(data.profile);
    setChartFacts(data.chart_facts);
    setBalance(data.balance ?? balance);

    let updatedProfiles = data.profiles || [];
    if (!updatedProfiles || updatedProfiles.length === 0) {
      const exists = profiles.some((p) => p.id === data.profile.id);
      if (exists) {
        updatedProfiles = profiles.map((p) => (p.id === data.profile.id ? data.profile : p));
      } else {
        updatedProfiles = [...profiles, data.profile];
      }
    }
    setProfiles(updatedProfiles);

    localStorage.setItem(
      "melooha_user_data",
      JSON.stringify({
        user: mergedUser,
        profile: data.profile,
        profiles: updatedProfiles,
        chart_facts: data.chart_facts,
        balance: data.balance ?? balance,
      })
    );
    setOnboardingConfig({ show: false, mode: "edit", targetProfile: null });
  };

  const handleOpenAddMember = () => {
    setOnboardingConfig({ show: true, mode: "add_member", targetProfile: null });
  };

  const handleOpenEditProfile = (target = null) => {
    setOnboardingConfig({
      show: true,
      mode: "edit",
      targetProfile: target || profile,
    });
  };

  const handleTopupSuccess = (newBalance) => {
    setBalance(newBalance);
    setShowPaywall(false);
  };

  const handleSelectQuestionFromHome = (questionText) => {
    setSelectedQuestionPrompt(questionText);
    setActiveTab("ask");
  };

  // If user is not authenticated, render LoginView with animated moving questions
  if (!user) {
    return (
      <LoginView
        onLoginSuccess={handleLoginSuccess}
        lang={lang}
        setLang={setLang}
      />
    );
  }

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
        profile={profile}
        profiles={profiles}
        balance={balance}
        lang={lang}
        setLang={setLang}
        onOpenPaywall={() => setShowPaywall(true)}
        onEditProfile={handleOpenEditProfile}
        onAddMember={handleOpenAddMember}
        onSelectProfile={handleSelectProfile}
      />

      {/* Main View Area */}
      <main className="flex-1 overflow-x-hidden">
        {activeTab === "home" && (
          <HomeView
            user={user}
            chartFacts={chartFacts}
            profile={profile}
            lang={lang}
            onSelectQuestion={handleSelectQuestionFromHome}
            onGoToAsk={() => setActiveTab("ask")}
            onGoToRewards={() => setActiveTab("rewards")}
            onGoToMuhurta={() => setActiveTab("muhurta")}
          />
        )}

        {activeTab === "muhurta" && (
          <MuhurtaView
            user={user}
            profile={profile}
            chartFacts={chartFacts}
            lang={lang}
            onSelectQuestion={handleSelectQuestionFromHome}
          />
        )}

        {activeTab === "chart" && (
          <ChartView
            chartFacts={chartFacts}
            profile={profile}
            lang={lang}
            onSelectQuestion={handleSelectQuestionFromHome}
          />
        )}

        {activeTab === "rewards" && (
          <RewardsView
            user={user}
            profile={profile}
            balance={balance}
            lang={lang}
            onGoToHome={() => setActiveTab("home")}
            onRefreshBalance={() => user && refreshBalance(user.id)}
            onOpenPaywall={() => setShowPaywall(true)}
          />
        )}

        {activeTab === "reports" && (
          <ReportsView
            user={user}
            profile={profile}
            profiles={profiles}
            chartFacts={chartFacts}
            balance={balance}
            lang={lang}
            onOpenPaywall={() => setShowPaywall(true)}
            onSelectQuestion={handleSelectQuestionFromHome}
            onOpenOnboarding={handleOpenAddMember}
          />
        )}

        {/* AskView: Always kept mounted so tab-switching never cancels background generation */}
        <div className={activeTab === "ask" ? "block" : "hidden"}>
          <AskView
            user={user}
            profile={profile}
            chartFacts={chartFacts}
            balance={balance}
            lang={lang}
            onOpenPaywall={() => setShowPaywall(true)}
            onOpenEvidence={(fact) => setSelectedFact(fact)}
            onOpenHistory={() => setActiveTab("history")}
            initialQuestion={selectedQuestionPrompt}
            onQuestionCompleted={() => user && refreshBalance(user.id)}
            onStreamingStateChange={handleStreamingStateChange}
          />
        </div>

        {activeTab === "history" && (
          <HistoryView
            user={user}
            profile={profile}
            chartFacts={chartFacts}
            lang={lang}
            onOpenEvidence={(fact) => setSelectedFact(fact)}
          />
        )}

        {activeTab === "profile" && (
          <ProfileView
            user={user}
            profile={profile}
            profiles={profiles}
            chartFacts={chartFacts}
            balance={balance}
            lang={lang}
            setLang={setLang}
            onOpenPaywall={() => setShowPaywall(true)}
            onGoToHistory={() => setActiveTab("history")}
            onGoToMetrics={() => setActiveTab("metrics")}
            onGoToStyleGuide={() => setActiveTab("styleguide")}
            onEditProfile={(target) => handleOpenEditProfile(target || profile)}
            onAddMember={handleOpenAddMember}
            onSelectProfile={handleSelectProfile}
            onLogout={handleLogout}
          />
        )}

        {activeTab === "metrics" && <MetricsView lang={lang} />}

        {activeTab === "styleguide" && (
          <StyleGuideView onBack={() => setActiveTab("profile")} />
        )}

        {/* Floating Background Question Generation / Completed Toast */}
        {activeTab !== "ask" && (streamingInfo.isStreaming || streamingInfo.hasUnreadAnswer) && (
          <div
            onClick={() => {
              setActiveTab("ask");
              setStreamingInfo((prev) => ({ ...prev, hasUnreadAnswer: false }));
            }}
            className="fixed bottom-20 left-1/2 -translate-x-1/2 z-40 max-w-sm w-[92%] p-3 rounded-2xl bg-[#1C0D33]/95 border border-[#B21E68]/80 shadow-[0_8px_30px_rgba(178,30,104,0.45)] backdrop-blur-md flex items-center justify-between cursor-pointer hover:border-[#E5A93C] transition-all"
          >
            <div className="flex items-center gap-2.5 overflow-hidden">
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${
                  streamingInfo.isStreaming
                    ? "bg-gradient-to-tr from-[#931B58] to-[#E5A93C] animate-spin"
                    : "bg-gradient-to-tr from-emerald-600 to-teal-500"
                }`}
              >
                <Sparkles className="w-4 h-4 text-white" />
              </div>
              <div className="truncate">
                <div className="text-xs font-bold text-white flex items-center gap-1.5">
                  <span>
                    {streamingInfo.isStreaming
                      ? `Consulting for ${profile?.name || "you"}...`
                      : `✨ ${profile?.name ? `${profile.name}'s` : "Your"} reading is ready!`}
                  </span>
                </div>
                <div className="text-[11px] text-[#DDD5EE] truncate">
                  {streamingInfo.isStreaming
                    ? streamingInfo.streamStatus || "Synthesizing planetary facts..."
                    : "Click to view full grounded reading"}
                </div>
              </div>
            </div>
            <span className="text-xs font-bold text-[#FDE68A] shrink-0 pl-2">
              {streamingInfo.isStreaming ? "View →" : "Read →"}
            </span>
          </div>
        )}
      </main>

      {/* Bottom Navigation */}
      <BottomNav activeTab={activeTab} setActiveTab={setActiveTab} lang={lang} />

      {/* Modals */}
      {onboardingConfig.show && (
        <OnboardingModal
          user={user}
          profile={profile}
          mode={onboardingConfig.mode}
          targetProfile={onboardingConfig.targetProfile}
          onOnboardSuccess={handleOnboardSuccess}
          onClose={() => setOnboardingConfig({ show: false, mode: "edit", targetProfile: null })}
          canClose={!!profile || profiles.length > 0}
          lang={lang}
        />
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
