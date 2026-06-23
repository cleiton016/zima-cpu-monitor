import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import UnavailableMetricWarning from "./UnavailableMetricWarning";

describe("UnavailableMetricWarning", () => {
  it("renders temperature unavailable message", () => {
    render(<UnavailableMetricWarning type="temperature" />);

    expect(screen.getByText("Sensor de temperatura não disponível neste hardware.")).toBeInTheDocument();
  });

  it("renders power unavailable message", () => {
    render(<UnavailableMetricWarning type="power" />);

    expect(screen.getByText("Medição de energia não disponível neste hardware.")).toBeInTheDocument();
  });
});
