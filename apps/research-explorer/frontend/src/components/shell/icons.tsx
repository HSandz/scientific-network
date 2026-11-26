import React from "react";

/** Line icons from the approved mockup (24px grid, 1.6 stroke, round caps). */
const PATHS: Record<string, React.ReactNode> = {
  pulse: <path d="M3 12h4l2.5-6 4 12 2.5-6H21" />,
  ask: (
    <>
      <path d="M4 5h16v11H9l-5 4z" />
      <path d="M8.5 10.5h7" />
    </>
  ),
  trends: (
    <>
      <path d="M4 19V5" />
      <path d="M4 19h16" />
      <path d="m7 15 4-4 3 2 5-6" />
    </>
  ),
  topics: (
    <>
      <path d="M4 7h10l6 5-6 5H4z" />
      <circle cx="8" cy="12" r="1" />
    </>
  ),
  groups: (
    <>
      <path d="M4 20V9l8-5 8 5v11" />
      <path d="M9 20v-6h6v6" />
    </>
  ),
  map: (
    <>
      <circle cx="6" cy="7" r="2" />
      <circle cx="17" cy="6" r="2" />
      <circle cx="9" cy="16" r="2" />
      <circle cx="18" cy="16" r="2" />
      <circle cx="13" cy="11" r="1.5" />
    </>
  ),
  network: (
    <>
      <circle cx="5" cy="12" r="2" />
      <circle cx="19" cy="5" r="2" />
      <circle cx="19" cy="19" r="2" />
      <circle cx="12" cy="12" r="2" />
      <path d="M7 12h3M13.6 10.8l3.8-4.6M13.6 13.2l3.8 4.6" />
    </>
  ),
  explore: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="m15.5 8.5-2 5-5 2 2-5z" />
    </>
  ),
  about: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 11v6" />
      <path d="M12 7.5v.5" />
    </>
  ),
  more: (
    <>
      <circle cx="5" cy="12" r="1.3" />
      <circle cx="12" cy="12" r="1.3" />
      <circle cx="19" cy="12" r="1.3" />
    </>
  ),
  search: (
    <>
      <circle cx="11" cy="11" r="7" />
      <path d="m20 20-3.5-3.5" />
    </>
  ),
  moon: <path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5Z" />,
  sun: (
    <>
      <circle cx="12" cy="12" r="4" />
      <path d="M12 3v2M12 19v2M3 12h2M19 12h2M5.6 5.6l1.4 1.4M17 17l1.4 1.4M5.6 18.4 7 17M17 7l1.4-1.4" />
    </>
  ),
  send: <path d="M5 12h14M13 6l6 6-6 6" />,
  close: <path d="M6 6l12 12M18 6 6 18" />,
  chevronDown: <path d="m6 9 6 6 6-6" />,
  chevronRight: <path d="m9 6 6 6-6 6" />,
  chevronLeft: <path d="m15 6-6 6 6 6" />,
  check: <path d="M5 12.5 10 17 19 7" />,
  shield: (
    <>
      <path d="M12 3 4 6v6c0 4.5 3.4 8 8 9 4.6-1 8-4.5 8-9V6z" />
      <path d="m8.5 12 2.5 2.5 4.5-5" />
    </>
  ),
  warning: (
    <>
      <path d="M12 4 2.8 20h18.4z" />
      <path d="M12 10v4.5M12 17.2v.3" />
    </>
  ),
  sliders: (
    <>
      <path d="M4 7h10M18 7h2M4 17h4M12 17h8" />
      <circle cx="16" cy="7" r="2" />
      <circle cx="10" cy="17" r="2" />
    </>
  ),
  copy: (
    <>
      <rect x="8" y="8" width="12" height="12" rx="2" />
      <path d="M16 8V5a1 1 0 0 0-1-1H5a1 1 0 0 0-1 1v10a1 1 0 0 0 1 1h3" />
    </>
  ),
  external: (
    <>
      <path d="M14 4h6v6" />
      <path d="M20 4 11 13" />
      <path d="M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5" />
    </>
  ),
  plus: <path d="M12 5v14M5 12h14" />,
  trash: (
    <>
      <path d="M5 7h14" />
      <path d="M9 7V4h6v3" />
      <path d="M7 7l1 13h8l1-13" />
    </>
  ),
};

export type IconName = keyof typeof PATHS | string;

export const Icon: React.FC<{ name: IconName; className?: string; size?: number; strokeWidth?: number; title?: string }> = ({
  name,
  className,
  size = 20,
  strokeWidth = 1.6,
  title,
}) => (
  <svg
    viewBox="0 0 24 24"
    width={size}
    height={size}
    fill="none"
    stroke="currentColor"
    strokeWidth={strokeWidth}
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
    aria-hidden={title ? undefined : true}
    role={title ? "img" : undefined}
    aria-label={title}
    focusable="false"
  >
    {PATHS[name] ?? null}
  </svg>
);

export const BrandMark: React.FC<{ size?: number }> = ({ size = 22 }) => (
  <span
    aria-hidden="true"
    className="inline-block shrink-0"
    style={{
      width: size,
      height: size,
      borderRadius: size / 4.4,
      background: "linear-gradient(90deg, var(--cool) 0 33%, var(--neutral) 33% 66%, var(--heat) 66%)",
    }}
  />
);
