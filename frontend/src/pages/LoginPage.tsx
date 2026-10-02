import { Link } from "react-router-dom";

/** Skeleton Login Page — full implementation in Module 2. */
export default function LoginPage() {
  return (
    <div className="min-h-screen bg-surface-900 flex items-center justify-center px-4">
      <div className="card w-full max-w-md animate-slide-up">
        <div className="text-center mb-8">
          <span className="text-4xl font-extrabold gradient-text">VAYORA</span>
          <p className="text-slate-400 mt-2">Sign in to your account</p>
        </div>
        <form className="space-y-4">
          <div>
            <label className="block text-sm text-slate-400 mb-1">Email</label>
            <input type="email" className="input-field" placeholder="you@example.com" />
          </div>
          <div>
            <label className="block text-sm text-slate-400 mb-1">Password</label>
            <input type="password" className="input-field" placeholder="••••••••" />
          </div>
          <button type="submit" className="btn-primary w-full mt-2">
            Sign In
          </button>
        </form>
        <p className="text-center text-slate-500 text-sm mt-6">
          Don't have an account?{" "}
          <Link to="/register" className="text-primary-400 hover:underline">Register</Link>
        </p>
        <div className="mt-4 text-center">
          <span className="badge badge-demo">Module 2 — Auth not yet implemented</span>
        </div>
      </div>
    </div>
  );
}
