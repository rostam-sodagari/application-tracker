import { useEffect, useState } from "react";
import { api } from "../api/client";
import { StatTile } from "../components/StatTile";
import { statusBadgeClass } from "../utils/statusColors";
import { formatDate, formatRate } from "../utils/format";
import type { HomeStats } from "../types";

export function HomePage() {
  const [stats, setStats] = useState<HomeStats | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<HomeStats>("/api/home")
      .then(setStats)
      .catch((e) => setError(e instanceof Error ? e.message : String(e)));
  }, []);

  if (error) return <p className="text-red-600 dark:text-red-400">{error}</p>;
  if (!stats) return <p className="text-slate-500 dark:text-slate-400">Loading…</p>;

  const goalReached = stats.applied_this_week >= stats.weekly_goal_low;
  const progressPercent = stats.weekly_goal_high
    ? Math.min(100, Math.round((stats.applied_this_week / stats.weekly_goal_high) * 100))
    : 0;

  return (
    <div className="space-y-8">
      <section>
        <h2 className="mb-2 text-base font-semibold text-slate-900 dark:text-slate-100">This week</h2>
        <div className="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-800">
          <p className="text-sm text-slate-700 dark:text-slate-300">
            <strong className="text-lg">{stats.applied_this_week}</strong> application
            {stats.applied_this_week === 1 ? "" : "s"} sent in the last 7 days
            <span className="text-slate-400 dark:text-slate-500">
              {" "}
              (goal: {stats.weekly_goal_low}–{stats.weekly_goal_high})
            </span>
          </p>
          <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-slate-100 dark:bg-slate-700">
            <div
              className={`h-full rounded-full transition-all ${goalReached ? "bg-emerald-500" : "bg-indigo-500"}`}
              style={{ width: `${progressPercent}%` }}
            />
          </div>
        </div>
      </section>

      <section>
        <h2 className="mb-2 text-base font-semibold text-slate-900 dark:text-slate-100">Overview</h2>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <StatTile label="Total applications" value={stats.total_applications} />
          <StatTile label="Sent" value={stats.total_applied} />
          <StatTile label="Response rate" value={formatRate(stats.response_rate)} sublabel="of applications sent" />
          <StatTile label="Interview rate" value={formatRate(stats.interview_rate)} sublabel="of applications sent" />
        </div>
        <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-4">
          <StatTile label="Offer rate" value={formatRate(stats.offer_rate)} sublabel="of applications sent" />
        </div>
      </section>

      <section>
        <h2 className="mb-2 text-base font-semibold text-slate-900 dark:text-slate-100">Status funnel</h2>
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 md:grid-cols-5">
          {Object.entries(stats.funnel).map(([status, count]) => (
            <div
              key={status}
              className="rounded-md border border-slate-200 bg-white p-3 text-center dark:border-slate-700 dark:bg-slate-800"
            >
              <div className="text-xl font-semibold text-slate-900 dark:text-slate-100">{count}</div>
              <span className={`mt-1 inline-block rounded-full px-2 py-0.5 text-xs font-medium ${statusBadgeClass(status)}`}>
                {status}
              </span>
            </div>
          ))}
        </div>
      </section>

      <section>
        <h2 className="mb-2 text-base font-semibold text-slate-900 dark:text-slate-100">Follow-ups due</h2>
        {stats.due_follow_ups.length === 0 ? (
          <p className="text-slate-500 dark:text-slate-400">None due right now.</p>
        ) : (
          <ul className="space-y-1">
            {stats.due_follow_ups.map((a) => (
              <li key={a.id} className="font-medium text-red-600 dark:text-red-400">
                {a.company} — {a.role || "—"} (due {formatDate(a.follow_up_date)})
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
