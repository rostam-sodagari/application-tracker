import { useState, type FormEvent } from "react";
import { Navigate } from "react-router-dom";
import { authErrorMessage, useAuth } from "../auth/AuthContext";
import { ThemeToggle } from "../components/ThemeToggle";

const inputClass =
  "w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 dark:border-slate-600 dark:bg-slate-900 dark:text-slate-100";
const labelClass = "mb-1 block text-xs font-medium text-slate-600 dark:text-slate-400";

export function LoginPage() {
  const { mode, user, loading, login, register } = useAuth();
  const [isRegistering, setIsRegistering] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (loading) {
    return <div className="flex min-h-screen items-center justify-center text-slate-500 dark:text-slate-400">Loading…</div>;
  }

  if (user) {
    return <Navigate to="/" replace />;
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      if (isRegistering) {
        if (password.length < 8) throw new Error("password must be at least 8 characters");
        await register(email, password);
      } else {
        await login(email, password);
      }
    } catch (err) {
      setError(authErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="relative flex min-h-screen items-center justify-center bg-slate-50 px-4 dark:bg-slate-950">
      <div className="absolute right-4 top-4">
        <ThemeToggle />
      </div>
      <form
        onSubmit={handleSubmit}
        className="w-full max-w-sm space-y-4 rounded-xl border border-slate-200 bg-white p-8 shadow-sm dark:border-slate-700 dark:bg-slate-800"
      >
        <div>
          <h1 className="text-lg font-semibold text-slate-900 dark:text-slate-100">Application Tracker</h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            {isRegistering ? "Create an account to get started." : "Sign in to your account."}
          </p>
        </div>

        {error && (
          <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700 dark:bg-red-950 dark:text-red-300">{error}</p>
        )}

        <div>
          <label className={labelClass}>Email</label>
          <input
            type="email"
            required
            autoFocus
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className={inputClass}
          />
        </div>
        <div>
          <label className={labelClass}>Password</label>
          <input
            type="password"
            required
            minLength={isRegistering ? 8 : undefined}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className={inputClass}
          />
          {isRegistering && (
            <p className="mt-1 text-xs text-slate-400 dark:text-slate-500">At least 8 characters.</p>
          )}
        </div>

        <button
          type="submit"
          disabled={submitting}
          className="w-full rounded-md bg-indigo-600 px-3 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50 dark:bg-indigo-500 dark:hover:bg-indigo-400"
        >
          {submitting ? "Please wait…" : isRegistering ? "Create account" : "Sign in"}
        </button>

        <p className="text-center text-sm text-slate-500 dark:text-slate-400">
          {isRegistering ? "Already have an account?" : "Need an account?"}{" "}
          <button
            type="button"
            onClick={() => {
              setIsRegistering((v) => !v);
              setError(null);
            }}
            className="font-medium text-indigo-600 hover:underline dark:text-indigo-400"
          >
            {isRegistering ? "Sign in" : "Register"}
          </button>
        </p>

        {mode === "local" && (
          <p className="text-center text-xs text-slate-400 dark:text-slate-500">
            Running in local mode: your account and data stay on this server.
          </p>
        )}
      </form>
    </div>
  );
}
