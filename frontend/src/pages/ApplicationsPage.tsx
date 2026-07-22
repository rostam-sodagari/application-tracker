import { useEffect, useState } from "react";
import { api } from "../api/client";
import { ApplicationForm, applicationFormValuesToPayload, type ApplicationFormValues } from "../components/ApplicationForm";
import { ConfirmDialog } from "../components/ConfirmDialog";
import { Modal } from "../components/Modal";
import { StatusSelect } from "../components/StatusSelect";
import type { Application, ApplicationPage, CvVersion, Meta } from "../types";
import { formatDate, formatSalary } from "../utils/format";

const PAGE_SIZE = 20;
const SEARCH_DEBOUNCE_MS = 300;

export function ApplicationsPage() {
  const [meta, setMeta] = useState<Meta | null>(null);
  const [cvs, setCvs] = useState<CvVersion[]>([]);
  const [statusFilter, setStatusFilter] = useState("");
  const [keywordInput, setKeywordInput] = useState("");
  const [keyword, setKeyword] = useState("");
  const [page, setPage] = useState(0);

  const [applications, setApplications] = useState<Application[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [showAdd, setShowAdd] = useState(false);
  const [editingApp, setEditingApp] = useState<Application | null>(null);
  const [deletingApp, setDeletingApp] = useState<Application | null>(null);

  useEffect(() => {
    api.get<Meta>("/api/meta").then(setMeta).catch(() => {});
    api.get<CvVersion[]>("/api/cvs").then(setCvs).catch(() => {});
  }, []);

  useEffect(() => {
    const timeout = setTimeout(() => {
      setKeyword(keywordInput.trim());
      setPage(0);
    }, SEARCH_DEBOUNCE_MS);
    return () => clearTimeout(timeout);
  }, [keywordInput]);

  useEffect(() => {
    setPage(0);
  }, [statusFilter]);

  const refresh = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ page: String(page) });
      if (statusFilter) params.set("status", statusFilter);
      if (keyword) params.set("keyword", keyword);
      const result = await api.get<ApplicationPage>(`/api/applications?${params.toString()}`);
      setApplications(result.items);
      setTotal(result.total);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [statusFilter, keyword, page]);

  const statuses = meta?.application_statuses ?? ["Draft Ready", "Applied"];
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  const handleAdd = async (values: ApplicationFormValues) => {
    await api.post("/api/applications", applicationFormValuesToPayload(values));
    setShowAdd(false);
    api.get<CvVersion[]>("/api/cvs").then(setCvs).catch(() => {});
    refresh();
  };

  const handleEdit = async (values: ApplicationFormValues) => {
    if (!editingApp) return;
    await api.patch(`/api/applications/${editingApp.id}`, applicationFormValuesToPayload(values));
    setEditingApp(null);
    api.get<CvVersion[]>("/api/cvs").then(setCvs).catch(() => {});
    refresh();
  };

  const handleStatusChange = async (app: Application, status: string) => {
    await api.patch(`/api/applications/${app.id}`, { status });
    refresh();
  };

  const handleDelete = async () => {
    if (!deletingApp) return;
    await api.del(`/api/applications/${deletingApp.id}`);
    setDeletingApp(null);
    refresh();
  };

  return (
    <div className="space-y-6">
      <section className="flex flex-wrap items-end justify-between gap-3">
        <div className="flex flex-wrap items-center gap-2">
          <input
            type="search"
            placeholder="Search company or role…"
            value={keywordInput}
            onChange={(e) => setKeywordInput(e.target.value)}
            className="w-56 rounded-md border border-slate-300 bg-white px-2 py-1.5 text-sm text-slate-900 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
          />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="rounded-md border border-slate-300 bg-white px-2 py-1.5 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
          >
            <option value="">Any status</option>
            {statuses.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </div>
        <button
          onClick={() => setShowAdd(true)}
          className="rounded-md bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-700 dark:bg-indigo-500 dark:hover:bg-indigo-400"
        >
          + Add application
        </button>
      </section>

      {loading && <p className="text-slate-500 dark:text-slate-400">Loading…</p>}
      {error && <p className="text-red-600 dark:text-red-400">{error}</p>}

      <div className="overflow-x-auto rounded-md border border-slate-200 dark:border-slate-700">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-left dark:bg-slate-800">
            <tr>
              <th className="p-2">Company</th>
              <th className="p-2">Role</th>
              <th className="p-2">Location</th>
              <th className="p-2">Salary</th>
              <th className="p-2">Materials</th>
              <th className="p-2">Status</th>
              <th className="p-2">Follow-up</th>
              <th className="p-2">Applied</th>
              <th className="p-2"></th>
            </tr>
          </thead>
          <tbody>
            {applications.map((app) => (
              <tr key={app.id} className="border-t border-slate-100 dark:border-slate-800">
                <td className="p-2">{app.company}</td>
                <td className="p-2">
                  {app.job_url ? (
                    <a href={app.job_url} target="_blank" rel="noopener noreferrer" className="text-indigo-600 hover:underline dark:text-indigo-400">
                      {app.role || "—"}
                    </a>
                  ) : (
                    app.role || "—"
                  )}
                </td>
                <td className="p-2 whitespace-nowrap text-slate-600 dark:text-slate-300">
                  {app.location || "—"}
                  {app.remote_type && <span className="ml-1 text-xs text-slate-400 dark:text-slate-500">({app.remote_type})</span>}
                </td>
                <td className="p-2 whitespace-nowrap text-slate-600 dark:text-slate-300">
                  {formatSalary(app.salary_min, app.salary_max)}
                </td>
                <td className="p-2">
                  {app.cv_file_id && (
                    <a
                      href={`/cvs/open/${encodeURIComponent(app.cv_file_id)}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-indigo-600 hover:underline dark:text-indigo-400"
                    >
                      CV
                    </a>
                  )}
                  {app.cv_file_id && app.cover_letter_file_id && " · "}
                  {app.cover_letter_file_id && (
                    <a
                      href={`/cvs/open/${encodeURIComponent(app.cover_letter_file_id)}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-indigo-600 hover:underline dark:text-indigo-400"
                    >
                      Cover letter
                    </a>
                  )}
                  {!app.cv_file_id && !app.cover_letter_file_id && "—"}
                </td>
                <td className="p-2">
                  <StatusSelect value={app.status} options={statuses} onChange={(v) => handleStatusChange(app, v)} />
                </td>
                <td className="p-2 whitespace-nowrap text-slate-500 dark:text-slate-400">{formatDate(app.follow_up_date)}</td>
                <td className="p-2 whitespace-nowrap text-slate-500 dark:text-slate-400">{formatDate(app.date_applied)}</td>
                <td className="p-2 whitespace-nowrap">
                  <button onClick={() => setEditingApp(app)} className="mr-2 text-indigo-600 hover:underline dark:text-indigo-400">
                    Edit
                  </button>
                  <button onClick={() => setDeletingApp(app)} className="text-red-600 hover:underline dark:text-red-400">
                    Delete
                  </button>
                </td>
              </tr>
            ))}
            {!loading && applications.length === 0 && (
              <tr>
                <td colSpan={9} className="p-4 text-center text-slate-400 dark:text-slate-500">
                  No applications match this filter.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {total > 0 && (
        <div className="flex items-center justify-between text-sm text-slate-500 dark:text-slate-400">
          <span>
            {total} application{total === 1 ? "" : "s"} · page {page + 1} of {totalPages}
          </span>
          <div className="flex gap-2">
            <button
              onClick={() => setPage((p) => Math.max(0, p - 1))}
              disabled={page === 0}
              className="rounded-md border border-slate-300 px-2.5 py-1 disabled:opacity-40 dark:border-slate-600"
            >
              Previous
            </button>
            <button
              onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
              disabled={page >= totalPages - 1}
              className="rounded-md border border-slate-300 px-2.5 py-1 disabled:opacity-40 dark:border-slate-600"
            >
              Next
            </button>
          </div>
        </div>
      )}

      {showAdd && (
        <Modal title="Add application" onClose={() => setShowAdd(false)}>
          <ApplicationForm statuses={statuses} cvs={cvs} onSubmit={handleAdd} onCancel={() => setShowAdd(false)} />
        </Modal>
      )}
      {editingApp && (
        <Modal title={`Edit ${editingApp.company}`} onClose={() => setEditingApp(null)}>
          <ApplicationForm
            application={editingApp}
            statuses={statuses}
            cvs={cvs}
            onSubmit={handleEdit}
            onCancel={() => setEditingApp(null)}
          />
        </Modal>
      )}
      {deletingApp && (
        <ConfirmDialog
          title="Delete application"
          message={`Delete the application to ${deletingApp.company}? This only removes the tracked application, not the CV/cover letter files.`}
          confirmLabel="Delete"
          danger
          onConfirm={handleDelete}
          onCancel={() => setDeletingApp(null)}
        />
      )}
    </div>
  );
}
