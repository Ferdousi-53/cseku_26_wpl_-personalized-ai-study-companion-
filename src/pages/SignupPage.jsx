import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";

export default function SignupPage() {
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleSignup = (e) => {
    e.preventDefault();
    navigate("/onboarding");
  };

  return (
    <div className="auth-wrap">
      <div className="auth-card">
        <div className="brand-name" style={{ marginBottom: 2 }}>Create your account</div>
        <div className="brand-sub">শুরু করা যাক তোমার প্রস্তুতি</div>

        <form onSubmit={handleSignup}>
          <label className="field-label">Full Name</label>
          <input className="field-input" value={name} onChange={(e) => setName(e.target.value)} required />
          <label className="field-label">Email</label>
          <input type="email" className="field-input" value={email} onChange={(e) => setEmail(e.target.value)} required />
          <label className="field-label">Password</label>
          <input type="password" className="field-input" value={password} onChange={(e) => setPassword(e.target.value)} required />
          <button type="submit" className="btn-primary">Create Account</button>
        </form>
        <div className="auth-footer">
          Already have an account? <Link to="/login">Log in</Link>
        </div>
      </div>
    </div>
  );
}