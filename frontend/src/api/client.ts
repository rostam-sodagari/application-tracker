let currentToken: string | null = null;

/** Called by AuthContext whenever the Appwrite JWT is minted/refreshed/cleared. */
export function setAuthToken(token: string | null) {
  currentToken = token;
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const isForm = options.body instanceof FormData;
  const headers: Record<string, string> = {
    ...(isForm ? {} : { "Content-Type": "application/json" }),
    ...(currentToken ? { Authorization: `Bearer ${currentToken}` } : {}),
    ...((options.headers as Record<string, string>) || {}),
  };
  const res = await fetch(path, { ...options, headers });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? JSON.stringify(body);
    } catch {
      // response body wasn't JSON — fall back to statusText
    }
    throw new Error(`${res.status}: ${detail}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export const api = {
  get: <T,>(path: string) => request<T>(path),
  post: <T,>(path: string, body: unknown) => request<T>(path, { method: "POST", body: JSON.stringify(body) }),
  patch: <T,>(path: string, body: unknown) => request<T>(path, { method: "PATCH", body: JSON.stringify(body) }),
  del: (path: string) => request<void>(path, { method: "DELETE" }),
  upload: <T,>(path: string, formData: FormData) => request<T>(path, { method: "POST", body: formData }),
};
