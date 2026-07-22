const DATE_FORMATTER = new Intl.DateTimeFormat("en-GB", { day: "numeric", month: "short", year: "numeric" });
const DATE_ONLY_RE = /^(\d{4})-(\d{2})-(\d{2})$/;

/** Renders both date-only values (date_applied, follow_up_date) and full timestamps
 * (created_at, updated_at) as e.g. "22 Jul 2026". Date-only strings are built from their
 * year/month/day components directly rather than parsed as UTC, so the calendar date shown
 * never shifts by a day depending on the viewer's timezone. */
export function formatDate(value: string | null | undefined): string {
  if (!value) return "—";
  const dateOnly = DATE_ONLY_RE.exec(value);
  const date = dateOnly
    ? new Date(Number(dateOnly[1]), Number(dateOnly[2]) - 1, Number(dateOnly[3]))
    : new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return DATE_FORMATTER.format(date);
}

/** Renders a percentage ratio (0-1) as e.g. "42%", or a placeholder when there is no data yet. */
export function formatRate(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  return `${Math.round(value * 100)}%`;
}

export function formatSalary(min: number | null, max: number | null): string {
  if (min == null && max == null) return "—";
  const fmt = (n: number) => n.toLocaleString("en-GB");
  if (min != null && max != null) return min === max ? fmt(min) : `${fmt(min)}–${fmt(max)}`;
  return fmt((min ?? max) as number);
}
