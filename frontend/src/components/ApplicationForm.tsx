import { useState, type FormEvent } from "react";
import { api } from "../api/client";
import type { Application, CvVersion } from "../types";

export interface ApplicationFormValues {
  company: string;
  role: string;
  source: string;
  job_url: string;
  date_applied: string;
  status: string;
  follow_up_date: string;
  notes: string;
  salary_min: string;
  salary_max: string;
  location: string;
  remote_type: string;
  cv_file_id: string | null;
  cover_letter_file_id: string | null;
}

function toFormValues(app?: Application, defaultStatus = "Draft Ready"): ApplicationFormValues {
  return {
    company: app?.company ?? "",
    role: app?.role ?? "",
    source: app?.source ?? "",
    job_url: app?.job_url ?? "",
    date_applied: app?.date_applied ?? "",
    status: app?.status ?? defaultStatus,
    follow_up_date: app?.follow_up_date ?? "",
    notes: app?.notes ?? "",
    salary_min: app?.salary_min != null ? String(app.salary_min) : "",
    salary_max: app?.salary_max != null ? String(app.salary_max) : "",
    location: app?.location ?? "",
    remote_type: app?.remote_type ?? "",
    cv_file_id: app?.cv_file_id ?? null,
    cover_letter_file_id: app?.cover_letter_file_id ?? null,
  };
}

interface ApplicationFormProps {
  application?: Application;
  statuses: string[];
  cvs: CvVersion[];
  onSubmit: (values: ApplicationFormValues) => Promise<void>;
  onCancel: () => void;
}

const inputClass =
  "w-full rounded-md border border-slate-300 bg-white px-2 py-1.5 text-sm text-slate-900 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 dark:border-slate-600 dark:bg-slate-900 dark:text-slate-100";
const labelClass = "mb-1 block text-xs font-medium text-slate-600 dark:text-slate-400";
const fileInputClass =
  "block w-full text-sm text-slate-700 file:mr-3 file:rounded-md file:border-0 file:bg-slate-100 file:px-3 file:py-1.5 file:text-sm file:font-medium file:text-slate-700 hover:file:bg-slate-200 dark:text-slate-300 dark:file:bg-slate-700 dark:file:text-slate-100 dark:hover:file:bg-slate-600";
const REMOTE_TYPE_OPTIONS = ["", "Remote", "Hybrid", "Onsite"];

export function ApplicationForm({ application, statuses, cvs, onSubmit, onCancel }: ApplicationFormProps) {
  const [values, setValues] = useState<ApplicationFormValues>(() => toFormValues(application));
  const [cvFile, setCvFile] = useState<File | null>(null);
  const [coverLetterFile, setCoverLetterFile] = useState<File | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const set = <K extends keyof ApplicationFormValues>(key: K, val: ApplicationFormValues[K]) =>
    setValues((v) => ({ ...v, [key]: val }));

  const currentCvName = values.cv_file_id ? cvs.find((c) => c.file_id === values.cv_file_id)?.file_name : null;
  const currentCoverLetterName = values.cover_letter_file_id
    ? cvs.find((c) => c.file_id === values.cover_letter_file_id)?.file_name
    : null;

  const uploadIfNeeded = async (file: File | null): Promise<string | null> => {
    if (!file) return null;
    const formData = new FormData();
    formData.append("file", file);
    if (values.company) formData.append("company", values.company);
    const uploaded = await api.upload<CvVersion>("/api/cvs", formData);
    return uploaded.file_id;
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const [newCvFileId, newCoverLetterFileId] = await Promise.all([
        uploadIfNeeded(cvFile),
        uploadIfNeeded(coverLetterFile),
      ]);
      await onSubmit({
        ...values,
        cv_file_id: newCvFileId ?? values.cv_file_id,
        cover_letter_file_id: newCoverLetterFileId ?? values.cover_letter_file_id,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      {error && <p className="text-sm text-red-600 dark:text-red-400">{error}</p>}
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className={labelClass}>Company *</label>
          <input required className={inputClass} value={values.company} onChange={(e) => set("company", e.target.value)} />
        </div>
        <div>
          <label className={labelClass}>Role</label>
          <input className={inputClass} value={values.role} onChange={(e) => set("role", e.target.value)} />
        </div>
        <div className="col-span-2">
          <label className={labelClass}>Job posting URL</label>
          <input className={inputClass} value={values.job_url} onChange={(e) => set("job_url", e.target.value)} />
        </div>
        <div>
          <label className={labelClass}>Source</label>
          <input className={inputClass} value={values.source} onChange={(e) => set("source", e.target.value)} />
        </div>
        <div>
          <label className={labelClass}>Location</label>
          <input className={inputClass} value={values.location} onChange={(e) => set("location", e.target.value)} />
        </div>
        <div>
          <label className={labelClass}>Remote type</label>
          <select className={inputClass} value={values.remote_type} onChange={(e) => set("remote_type", e.target.value)}>
            {REMOTE_TYPE_OPTIONS.map((opt) => (
              <option key={opt} value={opt}>
                {opt || "Not specified"}
              </option>
            ))}
          </select>
        </div>
        <div className="col-span-2 flex gap-3">
          <div className="flex-1">
            <label className={labelClass}>Salary min</label>
            <input
              type="number"
              min={0}
              className={inputClass}
              value={values.salary_min}
              onChange={(e) => set("salary_min", e.target.value)}
            />
          </div>
          <div className="flex-1">
            <label className={labelClass}>Salary max</label>
            <input
              type="number"
              min={0}
              className={inputClass}
              value={values.salary_max}
              onChange={(e) => set("salary_max", e.target.value)}
            />
          </div>
        </div>
        <div>
          <label className={labelClass}>CV</label>
          <input
            type="file"
            accept=".pdf,.md,.docx"
            className={fileInputClass}
            onChange={(e) => setCvFile(e.target.files?.[0] ?? null)}
          />
          {currentCvName && !cvFile && (
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">Currently attached: {currentCvName}</p>
          )}
        </div>
        <div>
          <label className={labelClass}>Cover letter</label>
          <input
            type="file"
            accept=".pdf,.md,.docx"
            className={fileInputClass}
            onChange={(e) => setCoverLetterFile(e.target.files?.[0] ?? null)}
          />
          {currentCoverLetterName && !coverLetterFile && (
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">Currently attached: {currentCoverLetterName}</p>
          )}
        </div>
        <div>
          <label className={labelClass}>Date applied</label>
          <input type="date" className={inputClass} value={values.date_applied} onChange={(e) => set("date_applied", e.target.value)} />
        </div>
        <div>
          <label className={labelClass}>Status</label>
          <select className={inputClass} value={values.status} onChange={(e) => set("status", e.target.value)}>
            {statuses.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className={labelClass}>Follow-up date</label>
          <input
            type="date"
            className={inputClass}
            value={values.follow_up_date}
            onChange={(e) => set("follow_up_date", e.target.value)}
          />
        </div>
        <div className="col-span-2">
          <label className={labelClass}>Notes</label>
          <textarea className={inputClass} rows={3} value={values.notes} onChange={(e) => set("notes", e.target.value)} />
        </div>
      </div>
      <div className="flex justify-end gap-2 pt-2">
        <button
          type="button"
          onClick={onCancel}
          className="rounded-md border border-slate-300 px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-50 dark:border-slate-600 dark:text-slate-200 dark:hover:bg-slate-700"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={submitting}
          className="rounded-md bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50 dark:bg-indigo-500 dark:hover:bg-indigo-400"
        >
          {submitting ? "Saving…" : "Save"}
        </button>
      </div>
    </form>
  );
}

export function applicationFormValuesToPayload(values: ApplicationFormValues) {
  return {
    company: values.company,
    role: values.role || null,
    source: values.source || null,
    job_url: values.job_url || null,
    cv_file_id: values.cv_file_id || null,
    cover_letter_file_id: values.cover_letter_file_id || null,
    date_applied: values.date_applied || null,
    status: values.status,
    follow_up_date: values.follow_up_date || null,
    notes: values.notes || null,
    salary_min: values.salary_min ? Number(values.salary_min) : null,
    salary_max: values.salary_max ? Number(values.salary_max) : null,
    location: values.location || null,
    remote_type: values.remote_type || null,
  };
}
