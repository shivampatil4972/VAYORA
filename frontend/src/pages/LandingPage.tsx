import { Link } from "react-router-dom";

/**
 * VAYORA Landing Page — Module 0 Skeleton
 * Full implementation in Module 9 (Search) and beyond.
 */
export default function LandingPage() {
  return (
    <div className="min-h-screen bg-surface-900 flex flex-col">
      {/* Navbar */}
      <nav className="border-b border-surface-700 px-8 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center">
            <span className="text-white font-bold text-sm">V</span>
          </div>
          <span className="text-xl font-bold gradient-text">VAYORA</span>
        </div>
        <div className="flex items-center gap-3">
          <Link to="/login" className="btn-secondary text-sm">Sign In</Link>
          <Link to="/register" className="btn-primary text-sm">Get Started</Link>
        </div>
      </nav>

      {/* Hero */}
      <main className="flex-1 flex flex-col items-center justify-center text-center px-6 animate-fade-in">
        <div className="max-w-4xl">
          <div className="badge badge-info mb-6 mx-auto">
            AI-Powered Intercity Shared Mobility
          </div>
          <h1 className="text-6xl font-extrabold mb-6 leading-tight">
            Travel Smarter with{" "}
            <span className="gradient-text">VAYORA</span>
          </h1>
          <p className="text-slate-400 text-xl mb-10 max-w-2xl mx-auto leading-relaxed">
            Intelligent two-sided matching, reliability prediction, proactive recovery 
            and EV-aware routing — engineered to maximize successfully completed journeys.
          </p>
          <div className="flex items-center justify-center gap-4 flex-wrap">
            <Link to="/register" className="btn-primary text-lg px-8 py-4">
              Start Your Journey →
            </Link>
            <Link to="/login" className="btn-secondary text-lg px-8 py-4">
              Driver Portal
            </Link>
          </div>
        </div>

        {/* Feature Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-24 max-w-5xl w-full">
          {[
            {
              icon: "🧠",
              title: "SmartMatch AI",
              desc: "Two-sided matching that predicts both booking and acceptance probability for optimal pairings.",
            },
            {
              icon: "🛡️",
              title: "ReliabilityAI",
              desc: "Journey confidence scoring — know your ride's completion probability before you book.",
            },
            {
              icon: "⚡",
              title: "Recovery Intelligence",
              desc: "Proactive backup candidates prepared before cancellations happen, not after.",
            },
          ].map((f) => (
            <div key={f.title} className="card text-left animate-slide-up">
              <div className="text-3xl mb-3">{f.icon}</div>
              <h3 className="text-white font-bold text-lg mb-2">{f.title}</h3>
              <p className="text-slate-400 text-sm leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-surface-700 px-8 py-4 text-center text-slate-500 text-sm">
        VAYORA — Research Prototype · Phase 1 Module 0 ·{" "}
        <span className="badge badge-demo">SKELETON</span>
      </footer>
    </div>
  );
}
