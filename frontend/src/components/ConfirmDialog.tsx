import { Modal } from "./Modal";

interface ConfirmDialogProps {
  title: string;
  message: string;
  confirmLabel?: string;
  danger?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

export function ConfirmDialog({ title, message, confirmLabel = "Confirm", danger, onConfirm, onCancel }: ConfirmDialogProps) {
  return (
    <Modal title={title} onClose={onCancel}>
      <p className="mb-4 text-sm text-slate-600 dark:text-slate-300">{message}</p>
      <div className="flex justify-end gap-2">
        <button
          onClick={onCancel}
          className="rounded-md border border-slate-300 px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-50 dark:border-slate-600 dark:text-slate-200 dark:hover:bg-slate-700"
        >
          Cancel
        </button>
        <button
          onClick={onConfirm}
          className={`rounded-md px-3 py-1.5 text-sm text-white ${
            danger ? "bg-red-600 hover:bg-red-700" : "bg-indigo-600 hover:bg-indigo-700"
          }`}
        >
          {confirmLabel}
        </button>
      </div>
    </Modal>
  );
}
