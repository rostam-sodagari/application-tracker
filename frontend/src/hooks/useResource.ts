import { useCallback, useEffect, useState } from "react";
import { api } from "../api/client";

export function useResource<T>(endpoint: string, query?: Record<string, string>) {
  const [data, setData] = useState<T[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const queryKey = query ? JSON.stringify(query) : "";

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const qs = query ? `?${new URLSearchParams(query).toString()}` : "";
      const result = await api.get<T[]>(`${endpoint}${qs}`);
      setData(result);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [endpoint, queryKey]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { data, loading, error, refresh };
}
