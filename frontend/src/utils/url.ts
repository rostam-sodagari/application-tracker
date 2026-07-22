/** True only for http(s) URLs. Used before rendering user-entered text (e.g. a job posting URL)
 * as a clickable link, so a value like `javascript:...` is shown as plain text instead of
 * becoming an executable href. */
export function isHttpUrl(value: string | null | undefined): boolean {
  if (!value) return false;
  try {
    return ["http:", "https:"].includes(new URL(value).protocol);
  } catch {
    return false;
  }
}
