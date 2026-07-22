interface StatTileProps {
  label: string;
  value: string | number;
  sublabel?: string;
}

export function StatTile({ label, value, sublabel }: StatTileProps) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-800">
      <div className="text-2xl font-semibold text-slate-900 dark:text-slate-100">{value}</div>
      <div className="mt-1 text-xs font-medium text-slate-500 dark:text-slate-400">{label}</div>
      {sublabel && <div className="mt-0.5 text-xs text-slate-400 dark:text-slate-500">{sublabel}</div>}
    </div>
  );
}
