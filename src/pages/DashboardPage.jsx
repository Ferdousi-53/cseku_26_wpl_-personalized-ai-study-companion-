import Sidebar from "../components/Sidebar";

export default function DashboardPage() {
  const tasks = [
    { s: "Physics — Kinematics", t: "1h", done: true },
    { s: "Math — Integration", t: "1h", done: true },
    { s: "Chemistry — Bonding", t: "1h", done: false },
    { s: "Practice — PYQ", t: "1h", done: false },
  ];

  return (
    <div className="app-shell">
      <Sidebar />
      <div className="main-area">
        <div className="topbar">
          <div>
            <div className="greet">Good Morning, Snigdha 👋</div>
            <div className="greet-sub">Engineering Admission</div>
          </div>
        </div>

        <div className="highlight-strip">
          <span className="num">120</span> days remaining
        </div>

        <div className="grid-2">
          <div>
            <div className="card">
              <div className="card-head">
                <span className="card-title">Today's Progress</span>
                <span className="mono-stat">72%</span>
              </div>
              <div className="bar-track"><div className="bar-fill" style={{ width: "72%" }} /></div>
              <div className="card-foot">3 / 5 Tasks Completed</div>
            </div>

            <div className="card">
              <div className="card-head"><span className="card-title">Today's Study Plan</span></div>
              {tasks.map((task) => (
                <div className="task-row" key={task.s}>
                  <div className={"task-check" + (task.done ? " done" : "")} />
                  <span className={"task-title" + (task.done ? " task-done-text" : "")}>{task.s}</span>
                  <span className="task-time">{task.t}</span>
                </div>
              ))}
            </div>
          </div>

          <div>
            <div className="card">
              <div className="card-head"><span className="card-title">Quick Access</span></div>
              <div className="quick-grid">
                <div className="quick-tile">🤖 Ask AI</div>
                <div className="quick-tile">📊 PYQ Analysis</div>
                <div className="quick-tile">📁 Materials</div>
                <div className="quick-tile">📈 Progress</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}