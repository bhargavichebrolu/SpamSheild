import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { DecisionGauge, gaugeLimit, GroupedBars, RatioBars, ShareBar, StackedBars } from "./Charts";

const SERIES = [
  { key: "a", name: "Alpha", color: "bg-ham" },
  { key: "b", name: "Beta", color: "bg-spam" },
];

describe("StackedBars", () => {
  const rows = [
    { label: "First", detail: "(10 messages)", values: { a: 30, b: 10 } },
    { label: "Second", values: { a: 5, b: 15 } },
    { label: "Empty", values: { a: 0, b: 0 } },
  ];

  it("writes every value as text, and has a legend", () => {
    render(<StackedBars label="Test chart" series={SERIES} rows={rows} />);
    const list = within(screen.getByRole("list", { name: "Test chart" }));
    expect(list.getByText("30 alpha, 10 beta")).toBeInTheDocument();
    expect(list.getByText("5 alpha, 15 beta")).toBeInTheDocument();
    expect(screen.getByText("Alpha")).toBeInTheDocument();
    expect(screen.getByText("Beta")).toBeInTheDocument();
  });

  it("draws rows on one shared scale, from zero", () => {
    const { container } = render(<StackedBars label="Test chart" series={SERIES} rows={rows} />);
    const bars = [...container.querySelectorAll<HTMLElement>('[aria-hidden="true"] > .flex')];
    expect(bars[0]?.style.width).toBe("100%");
    expect(bars[1]?.style.width).toBe("50%");
    expect(bars[2]?.style.width).toBe("0%");
  });

  it("sizes parts in proportion to their values", () => {
    const { container } = render(<StackedBars label="Test chart" series={SERIES} rows={[rows[0]!]} />);
    expect(container.querySelector<HTMLElement>('[title="Alpha: 30"]')?.style.flexGrow).toBe("30");
    expect(container.querySelector<HTMLElement>('[title="Beta: 10"]')?.style.flexGrow).toBe("10");
  });

  it("copes with no data at all", () => {
    render(<StackedBars label="Test chart" series={SERIES} rows={[]} />);
    expect(screen.getByRole("list", { name: "Test chart" })).toBeEmptyDOMElement();
  });
});

describe("RatioBars", () => {
  const rows = [
    { label: "High", value: 0.75, seriesKey: "a" },
    { label: "Low", value: 0.25, seriesKey: "b" },
  ];

  it("writes values as text, and starts its scale at zero", () => {
    const { container } = render(
      <RatioBars label="Test ratio" series={SERIES} rows={rows} scaleMax={1} formatValue={String} />,
    );
    expect(screen.getByText("0.75")).toBeInTheDocument();
    expect(container.querySelector<HTMLElement>('[title="High: 0.75"]')?.style.width).toBe("75%");
    expect(container.querySelector<HTMLElement>('[title="Low: 0.25"]')?.style.width).toBe("25%");
    expect(screen.getByText("0")).toBeInTheDocument();
    expect(screen.getByText("1")).toBeInTheDocument();
  });

  it("colours each bar by its series", () => {
    const { container } = render(
      <RatioBars label="Test ratio" series={SERIES} rows={rows} scaleMax={1} formatValue={String} />,
    );
    expect(container.querySelector('[title="High: 0.75"]')).toHaveClass("bg-ham");
    expect(container.querySelector('[title="Low: 0.25"]')).toHaveClass("bg-spam");
  });
});

describe("GroupedBars", () => {
  it("shows each series for each row, on one scale", () => {
    const { container } = render(
      <GroupedBars
        label="Test groups"
        series={SERIES}
        rows={[{ label: "Word", values: { a: 20, b: 10 } }]}
        formatValue={String}
      />,
    );
    expect(screen.getByText("Alpha 20")).toBeInTheDocument();
    expect(screen.getByText("Beta 10")).toBeInTheDocument();
    expect(container.querySelector<HTMLElement>('[title="Alpha: 20"]')?.style.width).toBe("100%");
    expect(container.querySelector<HTMLElement>('[title="Beta: 10"]')?.style.width).toBe("50%");
  });
});

describe("ShareBar", () => {
  it("names each part with its share, in text and for screen readers", () => {
    render(
      <ShareBar
        label="Test split"
        parts={[
          { name: "Big", value: 3, color: "bg-ham" },
          { name: "Small", value: 1, color: "bg-spam" },
        ]}
        formatPart={({ value }, whole) => `${value} of ${whole}`}
      />,
    );
    expect(screen.getByRole("img", { name: "Test split: Big, 3 of 4; Small, 1 of 4" })).toBeInTheDocument();
    expect(screen.getByText("Big: 3 of 4")).toBeInTheDocument();
  });
});

describe("DecisionGauge", () => {
  const marker = () => screen.getByTestId("gauge-marker").style.left;

  it("puts a score of zero on the boundary", () => {
    render(<DecisionGauge score={0} />);
    expect(marker()).toBe("50%");
  });

  it("puts positive scores on the spam side, and negative ones on the ham side", () => {
    const { unmount } = render(<DecisionGauge score={1} />);
    expect(marker()).toBe("75%");
    unmount();
    render(<DecisionGauge score={-1} />);
    expect(marker()).toBe("25%");
  });

  it("widens its scale so that a large score stays on the track", () => {
    expect(gaugeLimit(0.5)).toBe(2);
    expect(gaugeLimit(-2.2)).toBe(3);
    expect(gaugeLimit(7)).toBe(7);
    render(<DecisionGauge score={-7} />);
    expect(marker()).toBe("0%");
  });

  it("describes the score without a percentage or probability", () => {
    render(<DecisionGauge score={1.5} />);
    const gauge = screen.getByRole("img");
    expect(gauge).toHaveAccessibleName(/Decision score \+1\.500/);
    expect(gauge.getAttribute("aria-label")).not.toMatch(/%|probability|confidence/i);
    expect(gauge.textContent).not.toMatch(/%|probability|confidence/i);
  });
});
