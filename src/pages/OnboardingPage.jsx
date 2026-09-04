import { useState } from "react";
import { useNavigate } from "react-router-dom";

export default function OnboardingPage() {
  const navigate = useNavigate();
  const [goal, setGoal] = useState("University Admission");
  const goals = ["University Admission", "BCS", "University Courses"];

  return (
    <div className="auth-wrap">
      <div className="auth-card" style={{ maxWidth: 440 }}>
        <div className="onb-title">Welcome, Snigdha 👋</div>
        <div className="onb-sub">What are you preparing for?</div>

        <div className="radio-group">
          {goals.map((g) => (
            <div
              key={g}
              className={"radio-row" + (goal === g ? " active" : "")}
              onClick={() => setGoal(g)}
            >
              <div className="radio-dot" />
              {g}
            </div>
          ))}
        </div>

        <label className="field-label">Target Exam</label>
        <div className="select-box">Engineering Admission ▾</div>
        <label className="field-label">Exam Date</label>
        <div className="select-box">15 June 2027</div>
        <label className="field-label">Daily study time available</label>
        <div className="select-box">4 hours ▾</div>

        <button className="btn-primary" onClick={() => navigate("/dashboard")}>
          Continue →
        </button>
      </div>
    </div>
  );
}