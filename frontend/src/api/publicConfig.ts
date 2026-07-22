import type { PublicConfig } from "../types";

/** Unauthenticated: tells the app which backend is active before anyone has logged in. */
export async function getPublicConfig(): Promise<PublicConfig> {
  const res = await fetch("/api/public-config");
  if (!res.ok) throw new Error(`failed to load server configuration: ${res.status}`);
  return res.json();
}
