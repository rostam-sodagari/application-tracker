// One colour per application status, chosen to read clearly at a glance and to remain
// legible in both light and dark mode. Falls back to a neutral style for any status value
// not listed here, since the set of statuses is defined server-side and could grow.
const STATUS_STYLES: Record<string, string> = {
  Unknown: "bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-200",
  "Draft Ready": "bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-200",
  Applied: "bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300",
  Screening: "bg-amber-100 text-amber-700 dark:bg-amber-900 dark:text-amber-300",
  Interview: "bg-violet-100 text-violet-700 dark:bg-violet-900 dark:text-violet-300",
  "Final Round": "bg-fuchsia-100 text-fuchsia-700 dark:bg-fuchsia-900 dark:text-fuchsia-300",
  Offer: "bg-emerald-100 text-emerald-700 dark:bg-emerald-900 dark:text-emerald-300",
  Rejected: "bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300",
  Withdrawn: "bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400",
};
const DEFAULT_STATUS_STYLE = "bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-200";

export function statusBadgeClass(status: string): string {
  return STATUS_STYLES[status] ?? DEFAULT_STATUS_STYLE;
}
