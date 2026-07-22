import { useState } from "react";
import { authErrorMessage, useAuth } from "../auth/AuthContext";

export function VerificationBanner() {
  const { user, resendVerification } = useAuth();
  const [sent, setSent] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sending, setSending] = useState(false);

  if (!user || user.emailVerified) return null;

  const handleResend = async () => {
    setSending(true);
    setError(null);
    try {
      await resendVerification();
      setSent(true);
    } catch (err) {
      setError(authErrorMessage(err));
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="border-b border-amber-200 bg-amber-50 px-4 py-2 text-sm text-amber-800 dark:border-amber-900 dark:bg-amber-950 dark:text-amber-200">
      <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-2">
        <span>
          {sent ? "Verification email sent — check your inbox." : "Please verify your email address."}
          {error && <span className="ml-2 text-red-600 dark:text-red-400">{error}</span>}
        </span>
        {!sent && (
          <button
            onClick={handleResend}
            disabled={sending}
            className="font-medium underline decoration-dotted hover:decoration-solid disabled:opacity-50"
          >
            {sending ? "Sending…" : "Resend email"}
          </button>
        )}
      </div>
    </div>
  );
}
