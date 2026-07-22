import { useRef, useState } from "react";
import { api } from "../api/client";
import { ConfirmDialog } from "../components/ConfirmDialog";
import { useResource } from "../hooks/useResource";
import type { CvVersion } from "../types";
import { formatDate } from "../utils/format";

export function CvsPage() {
  const { data: cvs, loading, error, refresh } = useResource<CvVersion>("/api/cvs");
  const [deletingCv, setDeletingCv] = useState<CvVersion | null>(null);
  const [editingCompanyId, setEditingCompanyId] = useState<string | null>(null);
  const [companyDraft, setCompanyDraft] = useState("");

  const [uploadCompany, setUploadCompany] = useState("");
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    const file = fileInputRef.current?.files?.[0];
    if (!file) return;
    setUploading(true);
    setUploadError(null);
    try {
      const formData = new FormData();
      formData.append("file", file);
      if (uploadCompany) formData.append("company", uploadCompany);
      await api.upload("/api/cvs", formData);
      setUploadCompany("");
      if (fileInputRef.current) fileInputRef.current.value = "";
      refresh();
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : String(err));
    } finally {
      setUploading(false);
    }
  };

  const startEditCompany = (cv: CvVersion) => {
    setEditingCompanyId(cv.id);
    setCompanyDraft(cv.company ?? "");
  };

  const saveCompany = async (cv: CvVersion) => {
    await api.patch(`/api/cvs/${cv.id}`, { company: companyDraft || null });
    setEditingCompanyId(null);
    refresh();
  };

  const handleDelete = async () => {
    if (!deletingCv) return;
    await api.del(`/api/cvs/${deletingCv.id}`);
    setDeletingCv(null);
    refresh();
  };

  return (
    <div className="space-y-6">
      <section>
        <h2 className="mb-2 text-base font-semibold text-slate-900 dark:text-slate-100">Upload a CV</h2>
        <form onSubmit={handleUpload} className="flex flex-wrap items-center gap-2">
          <input
            ref={fileInputRef}
            type="file"
            required
            className="text-sm text-slate-700 dark:text-slate-300"
          />
          <input
            placeholder="Company (optional)"
            value={uploadCompany}
            onChange={(e) => setUploadCompany(e.target.value)}
            className="rounded-md border border-slate-300 bg-white px-2 py-1.5 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
          />
          <button
            type="submit"
            disabled={uploading}
            className="rounded-md bg-indigo-600 px-3 py-1.5 text-sm text-white hover:bg-indigo-700 disabled:opacity-50"
          >
            {uploading ? "Uploading…" : "Upload"}
          </button>
        </form>
        {uploadError && <p className="mt-1 text-sm text-red-600">{uploadError}</p>}
      </section>

      {loading && <p className="text-slate-500">Loading…</p>}
      {error && <p className="text-red-600">{error}</p>}

      <div className="overflow-x-auto rounded-md border border-slate-200 dark:border-slate-700">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-left dark:bg-slate-800">
            <tr>
              <th className="p-2">File</th>
              <th className="p-2">Company</th>
              <th className="p-2">Added</th>
              <th className="p-2"></th>
            </tr>
          </thead>
          <tbody>
            {cvs.map((cv) => (
              <tr key={cv.id} className="border-t border-slate-100 dark:border-slate-800">
                <td className="p-2">
                  <a
                    href={`/cvs/open/${encodeURIComponent(cv.file_id)}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-indigo-600 hover:underline dark:text-indigo-400"
                  >
                    {cv.file_name}
                  </a>
                </td>
                <td className="p-2">
                  {editingCompanyId === cv.id ? (
                    <div className="flex items-center gap-1">
                      <input
                        autoFocus
                        value={companyDraft}
                        onChange={(e) => setCompanyDraft(e.target.value)}
                        onKeyDown={(e) => e.key === "Enter" && saveCompany(cv)}
                        className="rounded-md border border-slate-300 bg-white px-1.5 py-0.5 text-sm dark:border-slate-600 dark:bg-slate-900 dark:text-slate-100"
                      />
                      <button onClick={() => saveCompany(cv)} className="text-indigo-600 hover:underline dark:text-indigo-400">
                        Save
                      </button>
                      <button onClick={() => setEditingCompanyId(null)} className="text-slate-500 hover:underline">
                        Cancel
                      </button>
                    </div>
                  ) : (
                    <button onClick={() => startEditCompany(cv)} className="hover:underline">
                      {cv.company || <span className="text-slate-400">— set company</span>}
                    </button>
                  )}
                </td>
                <td className="p-2 whitespace-nowrap text-slate-500 dark:text-slate-400">{formatDate(cv.created_at)}</td>
                <td className="p-2 whitespace-nowrap">
                  <button onClick={() => setDeletingCv(cv)} className="text-red-600 hover:underline dark:text-red-400">
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {deletingCv && (
        <ConfirmDialog
          title="Delete CV"
          message={`Delete "${deletingCv.file_name}"? This removes the file from storage as well — it cannot be undone.`}
          confirmLabel="Delete"
          danger
          onConfirm={handleDelete}
          onCancel={() => setDeletingCv(null)}
        />
      )}
    </div>
  );
}
