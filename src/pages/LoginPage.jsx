import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";

export default function LoginPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleLogin = (e) => {
    e.preventDefault();
    navigate("/onboarding");
  };

  return (
    <div className="auth-wrap">
      <div className="auth-card">
        <div className="auth-logo">📘</div>
        <div className="brand-name">Study Companion</div>
        <div className="brand-sub">তোমার প্রস্তুতির সঙ্গী</div>

        <form onSubmit={handleLogin}>
          <label className="field-label">Email</label>
          <input
            type="email"
            className="field-input"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <label className="field-label">Password</label>
          <input
            type="password"
            className="field-input"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          <button type="submit" className="btn-primary">Log In</button>
        </form>
        <div className="auth-footer">
          Don't have an account? <Link to="/signup">Create one</Link>
        </div>
      </div>
    </div>
  );
}