import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import MetricCard from "./MetricCard";

describe("MetricCard", () => {
  it("renders title and value", () => {
    render(<MetricCard title="CPU" value="25%" detail="2 núcleos" />);

    expect(screen.getByText("CPU")).toBeInTheDocument();
    expect(screen.getByText("25%")).toBeInTheDocument();
    expect(screen.getByText("2 núcleos")).toBeInTheDocument();
  });
});
