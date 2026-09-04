import { BrowserRouter, Routes, Route } from "react-router-dom";
import LoginPage from "./pages/LoginPage";
import SignupPage from "./pages/SignupPage";
import OnboardingPage from "./pages/OnboardingPage";
import DashboardPage from "./pages/DashboardPage";
import Sidebar from "./components/Sidebar";

function ComingSoon({ title }) {
  return (
    <div className="app-shell">
      <Sidebar />
      <div className="main-area">
        <div className="coming-soon">
          <div className="coming-soon-title">{title}</div>
          <div>Coming soon — পরের sprint-এ</div>
        </div>
      </div>
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LoginPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />
        <Route path="/onboarding" element={<OnboardingPage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/subjects" element={<ComingSoon title="Subjects" />} />
        <Route path="/materials" element={<ComingSoon title="Materials" />} />
        <Route path="/ai" element={<ComingSoon title="AI Tutor" />} />
        <Route path="/pyq" element={<ComingSoon title="PYQ Analysis" />} />
        <Route path="/planner" element={<ComingSoon title="Planner" />} />
        <Route path="/progress" element={<ComingSoon title="Progress" />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;