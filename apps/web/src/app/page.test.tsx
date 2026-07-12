import { render, screen } from "@testing-library/react";
import { expect, test } from "vitest";
import Home from "./page";

test("renders the landing headline", () => {
  render(<Home />);
  const heading = screen.getByRole("heading", { level: 1 });
  expect(heading.textContent).toContain("Camerino");
});
