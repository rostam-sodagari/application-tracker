import { describe, expect, it } from "vitest";
import { formatDate, formatRate, formatSalary } from "./format";

describe("formatDate", () => {
  it("renders a date-only string as day month year", () => {
    expect(formatDate("2026-07-22")).toBe("22 Jul 2026");
  });

  it("renders a full timestamp as day month year", () => {
    expect(formatDate("2026-07-22T10:30:00.000Z")).toBe("22 Jul 2026");
  });

  it("returns a placeholder for null or undefined", () => {
    expect(formatDate(null)).toBe("—");
    expect(formatDate(undefined)).toBe("—");
    expect(formatDate("")).toBe("—");
  });

  it("does not shift a date-only value across a timezone boundary", () => {
    // A date-only string represents a calendar date, not an instant, so it must render the
    // same day regardless of the viewer's timezone offset.
    expect(formatDate("2026-01-01")).toBe("1 Jan 2026");
    expect(formatDate("2026-12-31")).toBe("31 Dec 2026");
  });

  it("falls back to the original string for an unparseable value", () => {
    expect(formatDate("not-a-date")).toBe("not-a-date");
  });
});

describe("formatRate", () => {
  it("renders a ratio as a whole-number percentage", () => {
    expect(formatRate(0.5)).toBe("50%");
    expect(formatRate(1)).toBe("100%");
    expect(formatRate(0)).toBe("0%");
  });

  it("returns a placeholder when there is no data yet", () => {
    expect(formatRate(null)).toBe("—");
    expect(formatRate(undefined)).toBe("—");
  });
});

describe("formatSalary", () => {
  it("returns a placeholder when neither bound is set", () => {
    expect(formatSalary(null, null)).toBe("—");
  });

  it("renders a range when both bounds are set", () => {
    expect(formatSalary(50000, 60000)).toBe("50,000–60,000");
  });

  it("renders a single figure when both bounds are equal", () => {
    expect(formatSalary(50000, 50000)).toBe("50,000");
  });

  it("renders whichever single bound is set", () => {
    expect(formatSalary(50000, null)).toBe("50,000");
    expect(formatSalary(null, 60000)).toBe("60,000");
  });
});
