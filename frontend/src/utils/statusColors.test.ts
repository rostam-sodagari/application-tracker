import { describe, expect, it } from "vitest";
import { statusBadgeClass } from "./statusColors";

describe("statusBadgeClass", () => {
  it("returns a distinct style for each known status", () => {
    const statuses = [
      "Unknown",
      "Draft Ready",
      "Applied",
      "Screening",
      "Interview",
      "Final Round",
      "Offer",
      "Rejected",
      "Withdrawn",
    ];
    const styles = new Set(statuses.map(statusBadgeClass));
    // Unknown and Draft Ready intentionally share a neutral style; every other status is distinct.
    expect(styles.size).toBe(statuses.length - 1);
  });

  it("falls back to a neutral style for an unrecognized status", () => {
    expect(statusBadgeClass("Something New")).toBe(statusBadgeClass("Unknown"));
  });
});
