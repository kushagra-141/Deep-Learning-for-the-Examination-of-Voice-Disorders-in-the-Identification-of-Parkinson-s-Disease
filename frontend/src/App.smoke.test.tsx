/**
 * App.smoke.test.tsx — Phase 0 smoke test.
 * Verifies that <App /> mounts without crashing and contains the brand name.
 */
import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import App from "./App";

describe("App (smoke)", () => {
  it("renders the application heading", () => {
    render(<App />);
    expect(
      screen.getByRole("heading", { name: /parkinson/i }),
    ).toBeInTheDocument();
  });

  it("shows the medical disclaimer", () => {
    render(<App />);
    expect(screen.getByText(/NOT a diagnostic device/i)).toBeInTheDocument();
  });
});
