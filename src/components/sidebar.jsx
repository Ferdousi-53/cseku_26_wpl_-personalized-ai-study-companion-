import { NavLink, useNavigate } from "react-router-dom";

const navGroups = [
  {
    label: "Overview",
    items: [{ to: "/dashboard", label: "Dashboard" }],
  },
  {
    label: "Study",
    items: [
      { to: "/subjects", label: "Subjects" },
      { to: "/materials", label: "Materials" },
      { to: "/ai", label: "AI Tutor" },
    ],
  },
  {
    label: "Exam Prep",
    items: [
      { to: "/pyq", label: "PYQ Analysis" },
      { to: "/planner", label: "Planner" },
      { to: "/progress", label: "Progress" },
    ],
  },
];

export default function Sidebar() {
  const navigate = useNavigate();

  return (
    <div className="sidebar">
      <div className="sidebar-brand">
        <div className="auth-logo">📘</div>
        <div className="sidebar-brand-text">Study Companion</div>
      </div>

      {navGroups.map((group) => (
        <div key={group.label}>
          <div className="nav-section-label">{group.label}</div>
          {group.items.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) => "nav-item" + (isActive ? " active" : "")}
            >
              {item.label}
            </NavLink>
          ))}
        </div>
      ))}

      <div className="sidebar-footer">
        <div className="sidebar-user">
          <div className="sidebar-avatar">S</div>
          <div>
            <div className="sidebar-user-name">Snigdha</div>
            <div className="sidebar-user-role">Engineering Admission</div>
          </div>
        </div>
        <button className="logout-btn" onClick={() => navigate("/login")}>
          Log out
        </button>
      </div>
    </div>
  );
}