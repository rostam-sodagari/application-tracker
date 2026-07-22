import { statusBadgeClass } from "../utils/statusColors";

interface StatusSelectProps {
  value: string;
  options: string[];
  onChange: (value: string) => void;
  className?: string;
}

export function StatusSelect({ value, options, onChange, className = "" }: StatusSelectProps) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className={`rounded-full border-0 px-2.5 py-1 text-xs font-medium ${statusBadgeClass(value)} ${className}`}
    >
      {options.map((opt) => (
        <option key={opt} value={opt} className="bg-white text-slate-900 dark:bg-slate-800 dark:text-slate-100">
          {opt}
        </option>
      ))}
    </select>
  );
}
