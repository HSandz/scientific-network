import React, { useEffect, useRef } from "react";
import { useExplorerStore } from "../../stores/useExplorerStore";
const sections = [
  ["overview", "Overview"],
  ["quality", "Quality"],
  ["robustness", "Evidence sensitivity"],
  ["topics", "Topic evolution"],
  ["communities", "Communities"],
  ["sectors", "Sectors"],
  ["trajectories", "Citations"],
];
export const DashboardSection: React.FC<{
  id: string;
  title: string;
  description: string;
  children: React.ReactNode;
}> = ({ id, title, description, children }) => (
  <section
    id={`analytics-${id}`}
    data-analytics-section={id}
    className="analytics-section"
    aria-labelledby={`heading-${id}`}
  >
    <header className="analytics-section-heading">
      <h2
        id={`heading-${id}`}
        tabIndex={-1}
        className="text-xl font-semibold tracking-tight"
      >
        {title}
      </h2>
      <p className="text-sm text-muted mt-1">{description}</p>
    </header>
    {children}
  </section>
);
export const DashboardNav: React.FC<{ section: string }> = ({ section }) => {
  const nav = useRef<HTMLElement>(null);
  const observedSection = useRef(section);
  const scrollTo = (id: string, focus = false) => {
    const target = document.getElementById(`analytics-${id}`);
    if (id === "overview") {
      nav.current
        ?.closest("[data-testid=analytics-view]")
        ?.scrollTo({ top: 0 });
      return;
    }
    target?.scrollIntoView({ block: "start", behavior: "instant" });
    if (focus)
      target?.querySelector<HTMLElement>("h2")?.focus({ preventScroll: true });
  };
  useEffect(() => {
    const frame = requestAnimationFrame(() => scrollTo(section));
    return () => cancelAnimationFrame(frame);
  }, []);
  useEffect(() => {
    if (observedSection.current !== section) {
      observedSection.current = section;
      scrollTo(section);
    }
  }, [section]);
  useEffect(() => {
    const root = nav.current?.closest('[data-testid="analytics-view"]');
    if (!root) return;
    let frame = 0;
    const update = () => {
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(() => {
        const top =
          root.getBoundingClientRect().top +
          (nav.current?.offsetHeight || 0) +
          50;
        const current = [
          ...root.querySelectorAll<HTMLElement>("[data-analytics-section]"),
        ]
          .filter((el) => el.getBoundingClientRect().top <= top)
          .at(-1);
        if (
          current &&
          useExplorerStore.getState().analyticsSection !==
            current.dataset.analyticsSection
        ) {
          observedSection.current = current.dataset.analyticsSection!;
          useExplorerStore.setState({
            analyticsSection: current.dataset.analyticsSection!,
          });
        }
      });
    };
    root.addEventListener("scroll", update, { passive: true });
    return () => {
      root.removeEventListener("scroll", update);
      cancelAnimationFrame(frame);
    };
  }, []);
  return (
    <nav ref={nav} aria-label="Analytical sections" className="analytics-nav">
      {sections.map(([id, label]) => (
        <button
          key={id}
          className="ledger-btn ledger-btn-ghost"
          aria-pressed={section === id}
          onClick={() => {
            observedSection.current = id;
            useExplorerStore.setState({ analyticsSection: id });
            scrollTo(id, true);
          }}
        >
          {label}
        </button>
      ))}
    </nav>
  );
};
