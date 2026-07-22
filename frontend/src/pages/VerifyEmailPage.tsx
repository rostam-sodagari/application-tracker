import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { api } from "../api/client";
import { authErrorMessage, useAuth } from "../auth/AuthContext";
import { account } from "../auth/appwriteAuth";

type Status = "checking" | "success" | "error";

export function VerifyEmailPage() {
  const { mode, refresh } = useAuth();
  const [params] = useSearchParams();
  const [status, setStatus] = useState<Status>("checking");
  const [message, setMessage] = useState("Confirming your email address…");

  useEffect(() => {
    if (mode === null) return; // wait for backend mode to resolve first

    (async () => {
      try {
        if (mode === "appwrite") {
          const userId = params.get("userId");
          const secret = params.get("secret");
          if (!userId || !secret) throw new Error("this verification link is missing required parameters");
          await account.updateEmailVerification({ userId, secret });
        } else {
          const token = params.get("token");
          if (!token) throw new Error("this verification link is missing its token");
          await api.get(`/api/auth/verify-email?token=${encodeURIComponent(token)}`);
        }
        setStatus("success");
        setMessage("Your email address has been verified.");
        await refresh();
      } catch (err) {
        setStatus("error");
        setMessage(authErrorMessage(err));
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mode]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4 dark:bg-slate-950">
      <div className="w-full max-w-sm space-y-4 rounded-xl border border-slate-200 bg-white p-8 text-center shadow-sm dark:border-slate-700 dark:bg-slate-800">
        <h1 className="text-lg font-semibold text-slate-900 dark:text-slate-100">Email verification</h1>
        <p
          className={
            status === "error"
              ? "text-sm text-red-600 dark:text-red-400"
              : "text-sm text-slate-600 dark:text-slate-300"
          }
        >
          {message}
        </p>
        <Link to="/" className="inline-block text-sm font-medium text-indigo-600 hover:underline dark:text-indigo-400">
          Go to the application
        </Link>
      </div>
    </div>
  );
}
