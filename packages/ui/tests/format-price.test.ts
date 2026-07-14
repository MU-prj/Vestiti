import { describe, expect, it } from "vitest";

import { formatPrice } from "../src/index";

describe("formatPrice", () => {
  it("formats euro cents with the it-IT locale", () => {
    expect(formatPrice(12999, "EUR")).toContain("129,99");
  });

  it("formats other currencies", () => {
    expect(formatPrice(5000, "USD", "en-US")).toBe("$50.00");
  });
});
