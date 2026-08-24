import { useState } from "react";
import {
  Home, Calendar, Bot, TrendingUp, Bell, User, Upload, Search,
  Send, Sparkles, Check, Circle, ChevronRight, Flame, FolderOpen,
  FileText, ArrowLeft, BookOpen,
} from "lucide-react";

const SCREENS = [
  { id: "login", label: "Login" },
  { id: "onboarding", label: "Onboarding" },
  { id: "dashboard", label: "Dashboard" },
  { id: "materials", label: "Materials" },
  { id: "ai", label: "AI Tutor" },
  { id: "pyq", label: "PYQ Analysis" },
  { id: "planner", label: "Planner" },
  { id: "progress", label: "Progress" },
];

const TAB_SCREENS = ["dashboard", "planner", "ai", "progress"];

function Highlight({ children, style }) {
  return <span className="hl-mark" style={style}>{children}</span>;
}

function Bar({ pct, color }) {
  return (
    <div className="bar-track">
      <div className="bar-fill" style={{ width: `${pct}%`, background: color }} />
    </div>
  );
}

function TopChips({ current, onPick }) {
  return (
    <div className="topchips">
      {SCREENS.map((s) => (
        <button
          key={s.id}
          className={"chip" + (current === s.id ? " chip-active" : "")}
          onClick={() => onPick(s.id)}
        >
          {s.label}
        </button>
      ))}
    </div>
  );
}

function BottomNav({ current, onPick }) {
  const items = [
    { id: "dashboard", icon: Home, label: "Home" },
    { id: "planner", icon: Calendar, label: "Planner" },
    { id: "ai", icon: Bot, label: "AI" },
    { id: "progress", icon: TrendingUp, label: "Progress" },
  ];
  return (
    <div className="bottomnav">
      {items.map((it) => {
        const Icon = it.icon;
        const active = current === it.id;
        return (
          <button
            key={it.id}
            className={"navitem" + (active ? " navitem-active" : "")}
            onClick={() => onPick(it.id)}
          >
            <Icon size={20} strokeWidth={active ? 2.4 : 1.8} />
            <span>{it.label}</span>
          </button>
        );
      })}
    </div>
  );
}

// ---------- SCREENS ----------

function LoginScreen({ go }) {
  return (
    <div className="screen login-screen">
      <div className="login-logo">
        <BookOpen size={30} strokeWidth={2} />
      </div>
      <div className="brand-name">Study Companion</div>
      <div className="brand-sub">তোমার প্রস্তুতির সঙ্গী</div>

      <label className="field-label">Email</label>
      <div className="input-box" />
      <label className="field-label">Password</label>
      <div className="input-box" />

      <button className="btn-primary" style={{ marginTop: 22 }} onClick={() => go("onboarding")}>
        Login
      </button>
      <div className="link-text">Create Account</div>
    </div>
  );
}

function OnboardingScreen({ go }) {
  const [goal, setGoal] = useState("Engineering Admission");
  return (
    <div className="screen">
      <div className="onb-welcome">Welcome, Snigdha 👋</div>
      <div className="onb-question">What are you preparing for?</div>

      <div className="radio-group">
        {["University Admission", "BCS", "University Courses"].map((g) => (
          <div
            key={g}
            className={"radio-row" + (goal.includes(g.split(" ")[0]) ? " radio-row-active" : "")}
            onClick={() => setGoal(g)}
          >
            <div className="radio-dot" />
            {g}
          </div>
        ))}
      </div>

      <label className="field-label" style={{ marginTop: 18 }}>Target Exam</label>
      <div className="select-box">Engineering Admission ▾</div>

      <label className="field-label">Exam Date</label>
      <div className="select-box">15 June 2027</div>

      <label className="field-label">How much time can you study daily?</label>
      <div className="select-box">4 hours ▾</div>

      <button className="btn-primary" style={{ marginTop: 24 }} onClick={() => go("dashboard")}>
        Continue →
      </button>
    </div>
  );
}

function DashboardScreen({ go }) {
  const tasks = [
    { s: "Physics — Kinematics", t: "1h", done: true },
    { s: "Math — Integration", t: "1h", done: true },
    { s: "Chemistry — Bonding", t: "1h", done: false },
    { s: "Practice — PYQ", t: "1h", done: false },
  ];
  return (
    <div className="screen">
      <div className="dash-header">
        <div>
          <div className="dash-greet">Good Morning 👋</div>
          <div className="dash-exam">Engineering Admission</div>
        </div>
        <div className="dash-icons">
          <Bell size={18} />
          <User size={18} />
        </div>
      </div>

      <Highlight style={{ marginTop: 10 }}>
        <span className="days-num">120</span> days remaining
      </Highlight>

      <div className="card" style={{ marginTop: 16 }}>
        <div className="card-title-row">
          <span>Today's Progress</span>
          <span className="mono">72%</span>
        </div>
        <Bar pct={72} color="var(--amber)" />
        <div className="card-sub">3 / 5 Tasks Completed</div>
      </div>

      <div className="card" style={{ marginTop: 14 }}>
        <div className="card-title-row"><span>Today's Study Plan</span></div>
        {tasks.map((task) => (
          <div className="task-row" key={task.s}>
            {task.done ? <Check size={16} color="var(--sage)" /> : <Circle size={16} color="var(--muted)" />}
            <span className={task.done ? "task-done" : ""}>{task.s}</span>
            <span className="mono task-time">{task.t}</span>
          </div>
        ))}
      </div>

      <div className="quick-grid">
        <button className="quick-tile" onClick={() => go("ai")}>
          <Bot size={20} /> Ask AI
        </button>
        <button className="quick-tile" onClick={() => go("pyq")}>
          <TrendingUp size={20} /> PYQ Analysis
        </button>
        <button className="quick-tile" onClick={() => go("materials")}>
          <FolderOpen size={20} /> Materials
        </button>
        <button className="quick-tile" onClick={() => go("progress")}>
          <TrendingUp size={20} /> Progress
        </button>
      </div>
    </div>
  );
}

function MaterialsScreen() {
  const folders = [
    { name: "Physics", files: ["HSC Physics Notes.pdf", "Chapter 1.pdf", "Physics Formula.pdf"] },
    { name: "Mathematics", files: ["Calculus Notes.pdf", "Algebra.pdf"] },
    { name: "Chemistry", files: ["Organic Chemistry.pdf"] },
  ];
  return (
    <div className="screen">
      <div className="screen-title-row">
        <span className="screen-title">Study Materials</span>
        <button className="btn-small"><Upload size={14} /> Upload</button>
      </div>
      <div className="search-box"><Search size={15} color="var(--muted)" /> Search materials...</div>

      {folders.map((f) => (
        <div key={f.name} className="folder-block">
          <div className="folder-head"><FolderOpen size={16} color="var(--navy)" /> {f.name}</div>
          {f.files.map((file) => (
            <div key={file} className="file-row">
              <FileText size={14} color="var(--muted)" /> {file}
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}

function AiScreen() {
  return (
    <div className="screen">
      <div className="screen-title-row"><span className="screen-title">AI Study Assistant</span></div>
      <div className="ai-hint">Ask anything from your materials</div>

      <div className="ai-question-bubble">
        Explain Newton's 2nd Law with an example.
      </div>

      <div className="ai-answer-block">
        <div className="ai-answer-label"><Sparkles size={13} color="var(--amber)" /> AI</div>
        <div className="ai-answer-text">
          Newton's Second Law states that force equals mass times acceleration (F = ma)...
        </div>
        <div className="ai-answer-text" style={{ marginTop: 8, fontWeight: 600 }}>Example:</div>
        <div className="source-chips">
          <span className="source-chip"><FileText size={12} /> Physics Notes.pdf</span>
          <span className="source-chip"><FileText size={12} /> Chapter 2.pdf</span>
        </div>
        <div className="ai-action-row">
          <button className="btn-tiny">Explain More</button>
          <button className="btn-tiny">Give Example</button>
          <button className="btn-tiny">Practice Questions</button>
        </div>
      </div>

      <div className="chat-input-row">
        <div className="chat-input" />
        <button className="send-btn"><Send size={16} /></button>
      </div>
    </div>
  );
}

function PyqScreen() {
  const topics = [
    { name: "Kinematics", freq: 18, max: 18 },
    { name: "Dynamics", freq: 14, max: 18 },
    { name: "Electricity", freq: 11, max: 18 },
    { name: "Optics", freq: 9, max: 18 },
  ];
  const perf = [
    { t: "Kinematics", freq: "HIGH", perf: "LOW", color: "var(--coral)" },
    { t: "Dynamics", freq: "HIGH", perf: "GOOD", color: "var(--sage)" },
    { t: "Optics", freq: "MEDIUM", perf: "LOW", color: "var(--coral)" },
  ];
  return (
    <div className="screen">
      <div className="screen-title-row">
        <span className="screen-title">PYQ Analysis</span>
        <button className="btn-small"><Upload size={14} /> Upload</button>
      </div>
      <div className="card-sub" style={{ marginBottom: 8 }}>Physics — based on previous 10 years</div>

      {topics.map((tp) => (
        <div key={tp.name} className="pyq-row">
          <span className="pyq-label">{tp.name}</span>
          <div className="bar-track" style={{ flex: 1 }}>
            <div className="bar-fill" style={{ width: `${(tp.freq / tp.max) * 100}%`, background: "var(--navy)" }} />
          </div>
          <span className="mono pyq-freq">{tp.freq}</span>
        </div>
      ))}

      <div className="card" style={{ marginTop: 16 }}>
        <div className="card-title-row"><Flame size={15} color="var(--coral)" /> <span>High Priority Topics</span></div>
        <ol className="priority-list">
          <li>Kinematics</li>
          <li>Dynamics</li>
          <li>Electricity</li>
        </ol>
      </div>

      <div className="card" style={{ marginTop: 12 }}>
        <div className="card-title-row"><span>Topic vs Your Performance</span></div>
        {perf.map((p) => (
          <div className="perf-row" key={p.t}>
            <span>{p.t}</span>
            <span className="mono" style={{ color: "var(--muted)" }}>{p.freq}</span>
            <span className="perf-dot" style={{ color: p.color }}>● {p.perf}</span>
          </div>
        ))}
      </div>

      <button className="btn-primary" style={{ marginTop: 16 }}>Practice High Priority Topics</button>
    </div>
  );
}

function PlannerScreen() {
  const slots = [
    { time: "09:00", subj: "Physics", topic: "Kinematics", dur: "1 hour", done: false },
    { time: "11:00", subj: "Mathematics", topic: "Integration", dur: "1.5 hours", done: true },
    { time: "15:00", subj: "Chemistry", topic: "Chemical Bonding", dur: "1 hour", done: false },
    { time: "20:00", subj: "PYQ Practice", topic: "Physics", dur: "1.5 hours", done: false },
  ];
  return (
    <div className="screen">
      <div className="screen-title-row"><span className="screen-title">My Study Plan</span></div>
      <div className="card-sub">August 22 · Today's Goal: 5 hours</div>

      <div className="timeline">
        {slots.map((s) => (
          <div key={s.time} className="timeline-row">
            <div className="timeline-time mono">{s.time}</div>
            <div className="timeline-line">
              <div className={"timeline-dot" + (s.done ? " timeline-dot-done" : "")} />
              <div className="timeline-stick" />
            </div>
            <div className="timeline-body">
              <div className="timeline-subj">{s.subj}</div>
              <div className="timeline-topic">{s.topic} · {s.dur}</div>
              <div className={"timeline-status" + (s.done ? " status-done" : "")}>
                {s.done ? "✓ Completed" : "○ Not Started"}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function ProgressScreen() {
  const subs = [
    { name: "Physics", pct: 75, color: "var(--navy)" },
    { name: "Math", pct: 62, color: "var(--navy)" },
    { name: "Chemistry", pct: 80, color: "var(--navy)" },
  ];
  return (
    <div className="screen">
      <div className="screen-title-row"><span className="screen-title">My Progress</span></div>

      <div className="card-sub">Overall Preparation</div>
      <Highlight style={{ margin: "6px 0 4px" }}>
        <span className="days-num" style={{ fontSize: 26 }}>68%</span>
      </Highlight>
      <Bar pct={68} color="var(--amber)" />

      <div className="card" style={{ marginTop: 16 }}>
        <div className="card-title-row"><span>Subjects</span></div>
        {subs.map((s) => (
          <div key={s.name} style={{ marginBottom: 10 }}>
            <div className="card-title-row" style={{ fontSize: 12.5 }}>
              <span>{s.name}</span><span className="mono">{s.pct}%</span>
            </div>
            <Bar pct={s.pct} color={s.color} />
          </div>
        ))}
      </div>

      <div className="two-col">
        <div className="card">
          <div className="card-title-row" style={{ color: "var(--coral)" }}>Weak Topics 🔴</div>
          <ul className="plain-list">
            <li>Kinematics</li><li>Integration</li><li>Organic Chemistry</li>
          </ul>
        </div>
        <div className="card">
          <div className="card-title-row" style={{ color: "var(--sage)" }}>Strong Topics 🟢</div>
          <ul className="plain-list">
            <li>Mechanics</li><li>Algebra</li><li>Inorganic Chem.</li>
          </ul>
        </div>
      </div>

      <button className="btn-primary" style={{ marginTop: 14 }}>View Details</button>
    </div>
  );
}

// ---------- ROOT ----------

export default function StudyCompanionPrototype() {
  const [screen, setScreen] = useState("dashboard");

  const renderScreen = () => {
    switch (screen) {
      case "login": return <LoginScreen go={setScreen} />;
      case "onboarding": return <OnboardingScreen go={setScreen} />;
      case "dashboard": return <DashboardScreen go={setScreen} />;
      case "materials": return <MaterialsScreen />;
      case "ai": return <AiScreen />;
      case "pyq": return <PyqScreen />;
      case "planner": return <PlannerScreen />;
      case "progress": return <ProgressScreen />;
      default: return null;
    }
  };

  return (
    <div className="app-wrap">
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Fraunces:wght@500;600;700&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@500;600&display=swap');

        :root{
          --navy:#1B2A4A;
          --navy-deep:#101A30;
          --amber:#E8A33D;
          --sage:#5F9482;
          --coral:#D2542E;
          --paper:#F3F1EA;
          --card:#FFFFFF;
          --ink:#1E2430;
          --muted:#8A8F9C;
          --border:#E4E1D6;
        }
        *{box-sizing:border-box;}
        .app-wrap{
          font-family:'Inter',sans-serif;
          color:var(--ink);
          background:var(--paper);
          padding:24px 12px 40px;
          min-height:600px;
          display:flex;
          flex-direction:column;
          align-items:center;
          gap:16px;
        }
        .topchips{
          display:flex; gap:6px; flex-wrap:wrap; justify-content:center;
          max-width:380px;
        }
        .chip{
          font-family:'Inter',sans-serif;
          font-size:11.5px; font-weight:600;
          padding:6px 11px; border-radius:20px;
          border:1px solid var(--border);
          background:var(--card); color:var(--muted);
          cursor:pointer; transition:all .15s;
        }
        .chip-active{ background:var(--navy); color:#fff; border-color:var(--navy); }

        .phone{
          width:375px; max-width:92vw;
          background:var(--navy-deep);
          border-radius:38px;
          padding:12px;
          box-shadow:0 20px 45px rgba(16,26,48,0.28);
        }
        .phone-inner{
          background:var(--paper);
          border-radius:28px;
          overflow:hidden;
          display:flex; flex-direction:column;
          height:700px;
        }
        .notch{
          height:22px; display:flex; align-items:center; justify-content:center;
        }
        .notch::before{
          content:''; width:90px; height:6px; border-radius:6px; background:var(--navy-deep);
        }
        .screen-scroll{ flex:1; overflow-y:auto; }
        .screen{ padding:18px 18px 24px; }

        .field-label{ display:block; font-size:11.5px; color:var(--muted); margin:12px 0 5px; font-weight:600; }
        .input-box, .select-box{
          background:var(--card); border:1px solid var(--border); border-radius:10px;
          height:38px; display:flex; align-items:center; padding:0 12px; font-size:13px; color:var(--muted);
        }
        .select-box{ cursor:pointer; }
        .btn-primary{
          width:100%; background:var(--navy); color:#fff; border:none; border-radius:12px;
          padding:12px; font-weight:700; font-size:14px; cursor:pointer; font-family:'Inter',sans-serif;
        }
        .btn-primary:active{ opacity:.85; }
        .link-text{ text-align:center; margin-top:14px; font-size:12.5px; color:var(--navy); font-weight:600; text-decoration:underline; cursor:pointer; }

        .login-screen{ display:flex; flex-direction:column; align-items:center; padding-top:50px; }
        .login-logo{ width:56px; height:56px; border-radius:16px; background:var(--navy); color:#fff; display:flex; align-items:center; justify-content:center; margin-bottom:14px; }
        .brand-name{ font-family:'Fraunces',serif; font-weight:700; font-size:22px; }
        .brand-sub{ font-size:12px; color:var(--muted); margin-bottom:26px; }
        .login-screen .field-label, .login-screen .input-box{ width:100%; }

        .onb-welcome{ font-family:'Fraunces',serif; font-weight:600; font-size:19px; }
        .onb-question{ font-size:13.5px; color:var(--muted); margin:6px 0 14px; }
        .radio-group{ display:flex; flex-direction:column; gap:8px; }
        .radio-row{
          display:flex; align-items:center; gap:10px; padding:11px 13px;
          border:1px solid var(--border); border-radius:10px; background:var(--card);
          font-size:13px; cursor:pointer;
        }
        .radio-row-active{ border-color:var(--navy); background:#EEF1F7; font-weight:600; }
        .radio-dot{ width:14px; height:14px; border-radius:50%; border:2px solid var(--muted); }
        .radio-row-active .radio-dot{ border-color:var(--navy); background:var(--navy); }

        .dash-header{ display:flex; justify-content:space-between; align-items:flex-start; }
        .dash-greet{ font-family:'Fraunces',serif; font-weight:600; font-size:18px; }
        .dash-exam{ font-size:12.5px; color:var(--muted); margin-top:2px; }
        .dash-icons{ display:flex; gap:12px; color:var(--navy); margin-top:4px; }

        .hl-mark{ position:relative; display:inline-block; font-size:13.5px; font-weight:600; padding:2px 2px; }
        .hl-mark::before{
          content:''; position:absolute; left:-3px; right:-3px; bottom:1px; top:22%;
          background:var(--amber); opacity:.45; border-radius:3px; z-index:0;
        }
        .hl-mark > *{ position:relative; z-index:1; }
        .days-num{ font-family:'JetBrains Mono',monospace; font-weight:700; font-size:17px; }

        .card{ background:var(--card); border:1px solid var(--border); border-radius:14px; padding:14px; }
        .card-title-row{ display:flex; align-items:center; gap:6px; justify-content:space-between; font-size:13px; font-weight:700; margin-bottom:8px; }
        .card-sub{ font-size:11.5px; color:var(--muted); margin-top:6px; }
        .mono{ font-family:'JetBrains Mono',monospace; }

        .bar-track{ width:100%; height:7px; background:#EDEAE0; border-radius:6px; overflow:hidden; }
        .bar-fill{ height:100%; border-radius:6px; }

        .task-row{ display:flex; align-items:center; gap:8px; padding:7px 0; font-size:12.5px; border-top:1px solid var(--border); }
        .task-row:first-of-type{ border-top:none; }
        .task-done{ text-decoration:line-through; color:var(--muted); }
        .task-time{ margin-left:auto; color:var(--muted); font-size:11px; }

        .quick-grid{ display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-top:14px; }
        .quick-tile{
          display:flex; align-items:center; gap:8px; background:var(--card); border:1px solid var(--border);
          border-radius:12px; padding:13px; font-size:12.5px; font-weight:600; color:var(--navy); cursor:pointer;
        }

        .screen-title-row{ display:flex; justify-content:space-between; align-items:center; margin-bottom:10px; }
        .screen-title{ font-family:'Fraunces',serif; font-weight:600; font-size:18px; }
        .btn-small{ display:flex; align-items:center; gap:5px; background:var(--navy); color:#fff; border:none; border-radius:8px; padding:7px 10px; font-size:11.5px; font-weight:600; cursor:pointer; }
        .search-box{ display:flex; align-items:center; gap:6px; background:var(--card); border:1px solid var(--border); border-radius:10px; padding:9px 12px; font-size:12.5px; color:var(--muted); margin-bottom:14px; }

        .folder-block{ margin-bottom:12px; }
        .folder-head{ display:flex; align-items:center; gap:6px; font-weight:700; font-size:13px; margin-bottom:6px; }
        .file-row{ display:flex; align-items:center; gap:6px; font-size:12px; color:var(--muted); padding:4px 0 4px 22px; }

        .ai-hint{ font-size:12px; color:var(--muted); margin-bottom:10px; }
        .ai-question-bubble{ background:var(--navy); color:#fff; border-radius:12px 12px 3px 12px; padding:11px 13px; font-size:12.5px; margin-left:auto; margin-bottom:10px; max-width:85%; }
        .ai-answer-block{ background:var(--card); border:1px solid var(--border); border-radius:12px 12px 12px 3px; padding:13px; }
        .ai-answer-label{ display:flex; align-items:center; gap:5px; font-size:11px; font-weight:700; color:var(--amber); margin-bottom:6px; }
        .ai-answer-text{ font-size:12.5px; line-height:1.5; }
        .source-chips{ display:flex; gap:6px; margin-top:9px; flex-wrap:wrap; }
        .source-chip{ display:flex; align-items:center; gap:4px; background:var(--paper); border:1px solid var(--border); border-radius:8px; padding:4px 8px; font-size:10.5px; color:var(--muted); }
        .ai-action-row{ display:flex; gap:6px; margin-top:10px; flex-wrap:wrap; }
        .btn-tiny{ font-size:10.5px; font-weight:600; border:1px solid var(--navy); color:var(--navy); background:none; border-radius:16px; padding:5px 10px; cursor:pointer; }
        .chat-input-row{ display:flex; gap:8px; margin-top:16px; }
        .chat-input{ flex:1; height:38px; background:var(--card); border:1px solid var(--border); border-radius:19px; }
        .send-btn{ width:38px; height:38px; border-radius:50%; background:var(--navy); color:#fff; border:none; display:flex; align-items:center; justify-content:center; cursor:pointer; }

        .pyq-row{ display:flex; align-items:center; gap:10px; margin-bottom:9px; }
        .pyq-label{ width:78px; font-size:12px; flex-shrink:0; }
        .pyq-freq{ width:20px; text-align:right; font-size:12px; }
        .priority-list{ margin:0; padding-left:18px; font-size:12.5px; line-height:1.9; }
        .perf-row{ display:flex; justify-content:space-between; font-size:12px; padding:6px 0; border-top:1px solid var(--border); }
        .perf-row:first-of-type{ border-top:none; }
        .perf-dot{ font-weight:600; }

        .timeline{ margin-top:14px; }
        .timeline-row{ display:flex; gap:10px; }
        .timeline-time{ width:44px; font-size:11.5px; color:var(--muted); padding-top:2px; }
        .timeline-line{ display:flex; flex-direction:column; align-items:center; }
        .timeline-dot{ width:10px; height:10px; border-radius:50%; border:2px solid var(--muted); background:var(--paper); margin-top:4px; }
        .timeline-dot-done{ background:var(--sage); border-color:var(--sage); }
        .timeline-stick{ width:2px; flex:1; background:var(--border); margin:2px 0; }
        .timeline-body{ padding-bottom:20px; }
        .timeline-subj{ font-weight:700; font-size:13px; }
        .timeline-topic{ font-size:11.5px; color:var(--muted); margin:2px 0 4px; }
        .timeline-status{ font-size:11px; color:var(--muted); }
        .status-done{ color:var(--sage); font-weight:600; }

        .two-col{ display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-top:14px; }
        .plain-list{ margin:0; padding-left:16px; font-size:11.5px; line-height:1.8; color:var(--ink); }

        .bottomnav{
          display:flex; border-top:1px solid var(--border); background:var(--card);
        }
        .navitem{
          flex:1; display:flex; flex-direction:column; align-items:center; gap:3px;
          padding:10px 0 8px; background:none; border:none; cursor:pointer; color:var(--muted); font-size:10px; font-weight:600;
        }
        .navitem-active{ color:var(--navy); }
      `}</style>

      <TopChips current={screen} onPick={setScreen} />

      <div className="phone">
        <div className="phone-inner">
          <div className="notch" />
          <div className="screen-scroll">{renderScreen()}</div>
          {TAB_SCREENS.includes(screen) && <BottomNav current={screen} onPick={setScreen} />}
        </div>
      </div>
    </div>
  );
}
