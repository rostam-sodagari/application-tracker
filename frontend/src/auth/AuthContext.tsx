import { AppwriteException } from "appwrite";
import { createContext, useContext, useEffect, useRef, useState, type ReactNode } from "react";
import { api, setAuthToken } from "../api/client";
import { getPublicConfig } from "../api/publicConfig";
import type { BackendMode } from "../types";
import { account, ID } from "./appwriteAuth";

interface AuthUser {
  email: string;
  emailVerified: boolean;
}

interface AuthContextValue {
  mode: BackendMode | null;
  user: AuthUser | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  resendVerification: () => Promise<void>;
  /** Re-reads the current session's verification status, e.g. after confirming an email link
   * in the same browser. Silently does nothing if there is no active session here. */
  refresh: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

const LOCAL_TOKEN_KEY = "app_tracker_local_token";
// Appwrite JWTs expire after 15 minutes; refresh well before that so an in-progress session
// never has its token go stale mid-use.
const JWT_REFRESH_INTERVAL_MS = 10 * 60 * 1000;

function verificationRedirectUrl(): string {
  return `${window.location.origin}/verify-email`;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [mode, setMode] = useState<BackendMode | null>(null);
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);
  const refreshTimer = useRef<ReturnType<typeof setInterval> | null>(null);

  const stopRefreshLoop = () => {
    if (refreshTimer.current) {
      clearInterval(refreshTimer.current);
      refreshTimer.current = null;
    }
  };

  const mintJwt = async () => {
    const jwt = await account.createJWT();
    setAuthToken(jwt.jwt);
  };

  const startRefreshLoop = () => {
    stopRefreshLoop();
    refreshTimer.current = setInterval(() => {
      mintJwt().catch(() => {
        setAuthToken(null);
        setUser(null);
        stopRefreshLoop();
      });
    }, JWT_REFRESH_INTERVAL_MS);
  };

  const refreshAppwriteUser = async () => {
    const current = await account.get();
    await mintJwt();
    setUser({ email: current.email, emailVerified: current.emailVerification });
    startRefreshLoop();
  };

  const refreshLocalUser = async (token: string) => {
    setAuthToken(token);
    const who = await api.get<{ email: string; email_verified: boolean }>("/api/auth/whoami");
    setUser({ email: who.email, emailVerified: who.email_verified });
  };

  useEffect(() => {
    let cancelled = false;

    (async () => {
      const config = await getPublicConfig().catch(() => ({ backend_mode: "local" as BackendMode }));
      if (cancelled) return;
      setMode(config.backend_mode);

      try {
        if (config.backend_mode === "appwrite") {
          await refreshAppwriteUser();
        } else {
          const token = localStorage.getItem(LOCAL_TOKEN_KEY);
          if (!token) throw new Error("no stored session");
          await refreshLocalUser(token);
        }
      } catch {
        setAuthToken(null);
        localStorage.removeItem(LOCAL_TOKEN_KEY);
        setUser(null);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => {
      cancelled = true;
      stopRefreshLoop();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const login = async (email: string, password: string) => {
    if (mode === "appwrite") {
      await account.createEmailPasswordSession({ email, password });
      await refreshAppwriteUser();
    } else {
      const result = await api.post<{ token: string }>("/api/auth/login", { email, password });
      localStorage.setItem(LOCAL_TOKEN_KEY, result.token);
      await refreshLocalUser(result.token);
    }
  };

  const register = async (email: string, password: string) => {
    if (mode === "appwrite") {
      await account.create({ userId: ID.unique(), email, password });
      await account.createEmailPasswordSession({ email, password });
      try {
        await account.createEmailVerification({ url: verificationRedirectUrl() });
      } catch {
        // Registration itself succeeded; a verification send failure (for example, no email
        // provider configured on the Appwrite project) should not block the new account.
      }
      await refreshAppwriteUser();
    } else {
      const result = await api.post<{ token: string }>("/api/auth/register", { email, password });
      localStorage.setItem(LOCAL_TOKEN_KEY, result.token);
      await refreshLocalUser(result.token);
    }
  };

  const logout = async () => {
    stopRefreshLoop();
    if (mode === "appwrite") {
      try {
        await account.deleteSession({ sessionId: "current" });
      } catch {
        // Session may already be gone (expired/revoked elsewhere); clearing local state below
        // is what actually matters to the user.
      }
    } else {
      localStorage.removeItem(LOCAL_TOKEN_KEY);
      await api.post("/api/auth/logout", {}).catch(() => {});
    }
    setAuthToken(null);
    setUser(null);
  };

  const resendVerification = async () => {
    if (mode === "appwrite") {
      await account.createEmailVerification({ url: verificationRedirectUrl() });
    } else {
      await api.post("/api/auth/resend-verification", {});
    }
  };

  const refresh = async () => {
    try {
      if (mode === "appwrite") {
        await refreshAppwriteUser();
      } else {
        const token = localStorage.getItem(LOCAL_TOKEN_KEY);
        if (!token) return;
        await refreshLocalUser(token);
      }
    } catch {
      // No active session in this browser to refresh; nothing to do.
    }
  };

  return (
    <AuthContext.Provider value={{ mode, user, loading, login, register, logout, resendVerification, refresh }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

export function authErrorMessage(err: unknown): string {
  if (err instanceof AppwriteException) return err.message;
  if (err instanceof Error) return err.message;
  return String(err);
}
