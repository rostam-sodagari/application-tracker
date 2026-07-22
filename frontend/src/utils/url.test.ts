import { describe, expect, it } from "vitest";
import { isHttpUrl } from "./url";

describe("isHttpUrl", () => {
  it("accepts http and https URLs", () => {
    expect(isHttpUrl("http://example.com/job")).toBe(true);
    expect(isHttpUrl("https://example.com/job")).toBe(true);
  });

  it("rejects a javascript: URL", () => {
    expect(isHttpUrl("javascript:alert(document.cookie)")).toBe(false);
  });

  it("rejects other non-http schemes", () => {
    expect(isHttpUrl("data:text/html,<script>alert(1)</script>")).toBe(false);
    expect(isHttpUrl("file:///etc/passwd")).toBe(false);
  });

  it("rejects null, undefined, empty, and unparseable values", () => {
    expect(isHttpUrl(null)).toBe(false);
    expect(isHttpUrl(undefined)).toBe(false);
    expect(isHttpUrl("")).toBe(false);
    expect(isHttpUrl("not a url")).toBe(false);
  });
});
