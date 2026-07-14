import { describe, expect, it } from "vitest";

import { apiBaseUrl } from "../lib/api-url";

describe("apiBaseUrl", () => {
  it("falls back to localhost when NEXT_PUBLIC_API_URL is unset", () => {
    delete process.env.NEXT_PUBLIC_API_URL;
    expect(apiBaseUrl()).toBe("http://localhost:8000");
  });

  it("honours NEXT_PUBLIC_API_URL", () => {
    process.env.NEXT_PUBLIC_API_URL = "https://api.example.test";
    expect(apiBaseUrl()).toBe("https://api.example.test");
    delete process.env.NEXT_PUBLIC_API_URL;
  });
});
