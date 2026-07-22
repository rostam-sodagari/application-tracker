import { useEffect, useState, type FormEvent } from "react";
import { api } from "../api/client";
import type { Settings } from "../types";

export function SettingsPage() {
  const [low, setLow] = useState("");
  const [high, setHigh] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    api
      .get<Settings>("/api/settings")
      .then((s) => {
        setLow(String(s.weekly_goal_low));
        setHigh(String(s.weekly_goal_high));
      })
      .catch((e) => setError(e instanceof Error ? e.message : String(e)))
      .finally(() => setLoading(false));
  }, []);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setSaved(false);
    const weekly_goal_low = Number(low);
    const weekly_goal_high = Number(high);
    if (!Number.isInteger(weekly_goal_low) || !Number.isInteger(weekly_goal_high) || weekly_goal_low < 0) {
      setError("enter whole numbers, with the low end at least zero");
      return;
    }
    if (weekly_goal_high < weekly_goal_low) {
      setError("the high end of the goal cannot be less than the low end");
      return;
    }
    setSaving(true);
    try {
      await api.patch<Settings>("/api/settings", { weekly_goal_low, weekly_goal_high });
      setSaved(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <p className="text-slate-500 dark:text-slate-400">Loading…</p>;

  return (
    <div className="max-w-md space-y-6">
      <h1 className="text-lg font-semibold text-slate-900 dark:text-slate-100">Settings</h1>

      <form
        onSubmit={handleSubmit}
        className="space-y-4 rounded-lg border border-slate-200 bg-white p-6 dark:border-slate-700 dark:bg-slate-800"
      >
        <div>
          <h2 className="text-sm font-medium text-slate-900 dark:text-slate-100">Weekly application goal</h2>
          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
            Shown as your target range on the home page, applied against applications sent in the last 7 days.
          </p>
        </div>

        {error && <p className="text-sm text-red-600 dark:text-red-400">{error}</p>}
        {saved && !error && <p className="text-sm text-emerald-600 dark:text-emerald-400">Saved.</p>}

        <div className="flex items-center gap-3">
          <div>
            <label className="mb-1 block text-xs font-medium text-slate-600 dark:text-slate-400">Low end</label>
            <input
              type="number"
              min={0}
              required
              value={low}
              onChange={(e) => setLow(e.target.value)}
              className="w-24 rounded-md border border-slate-300 bg-white px-2 py-1.5 text-sm text-slate-900 dark:border-slate-600 dark:bg-slate-900 dark:text-slate-100"
            />
          </div>
          <span className="mt-5 text-slate-400">to</span>
          <div>
            <label className="mb-1 block text-xs font-medium text-slate-600 dark:text-slate-400">High end</label>
            <input
              type="number"
              min={0}
              required
              value={high}
              onChange={(e) => setHigh(e.target.value)}
              className="w-24 rounded-md border border-slate-300 bg-white px-2 py-1.5 text-sm text-slate-900 dark:border-slate-600 dark:bg-slate-900 dark:text-slate-100"
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={saving}
          className="rounded-md bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50 dark:bg-indigo-500 dark:hover:bg-indigo-400"
        >
          {saving ? "Saving…" : "Save"}
        </button>
      </form>
    </div>
  );
}
