import React, { useEffect, useId, useLayoutEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { linkClick } from "../../lib/router";
import { momentumInkVar, readPalette, rowHue, withAlpha } from "../../lib/thermal";
import { Icon } from "../shell/icons";

/* ---------- Entity hues: dots and chips only ---------- */
export const ENTITY_VAR: Record<string, string> = {
  Method: "var(--method)",
  Task: "var(--task)",
  Dataset: "var(--dataset)",
  Organization: "var(--org)",
  Researcher: "var(--researcher)",
  Topic: "var(--topic)",
  Paper: "var(--paper-node)",
  Venue: "var(--org)",
};

export const EntityDot: React.FC<{ kind?: string | null; size?: number }> = ({ kind, size = 8 }) => (
  <span
    aria-hidden="true"
    className="inline-block rounded-full shrink-0"
    style={{ width: size, height: size, background: ENTITY_VAR[kind || ""] || "var(--org)" }}
  />
);

/* ---------- Momentum chip ---------- */
const CLASS_WORD: Record<string, string> = {
  rising: "Rising",
  emerging: "Emerging",
  stable: "Stable",
  declining: "Declining",
};
export function classWord(cls?: string | null): string {
  return CLASS_WORD[cls || ""] || (cls ? cls[0].toUpperCase() + cls.slice(1) : "Not classified");
}

export const MomentumChip: React.FC<{ cls?: string | null; t: number; label?: string; title?: string }> = ({
  cls,
  t,
  label,
  title,
}) => {
  const p = readPalette();
  const hue = rowHue(t, p);
  return (
    <span
      className="momentum"
      title={title}
      data-momentum={cls || "unknown"}
      style={{
        // @ts-expect-error custom property
        "--m": hue,
        background: withAlpha(hue, p.dark ? 0.18 : 0.14),
        color: momentumInkVar(cls || "stable"),
      }}
    >
      {label || classWord(cls)}
    </span>
  );
};

/* ---------- In-app link ---------- */
export const AppLink: React.FC<
  React.AnchorHTMLAttributes<HTMLAnchorElement> & { to: string; className?: string }
> = ({ to, className, children, onClick, ...rest }) => (
  <a
    href={to}
    className={className}
    onClick={(e) => {
      onClick?.(e);
      linkClick(e, to);
    }}
    {...rest}
  >
    {children}
  </a>
);

/* ---------- ⓘ popover ---------- */
export const InfoPopover: React.FC<{ label?: string; children: React.ReactNode; testId?: string }> = ({
  label = "What does this mean?",
  children,
  testId,
}) => {
  const [open, setOpen] = useState(false);
  const [pos, setPos] = useState<{ left: number; top: number }>({ left: 0, top: 0 });
  const btnRef = useRef<HTMLButtonElement>(null);
  const popRef = useRef<HTMLDivElement>(null);
  const id = useId();

  const place = () => {
    const r = btnRef.current?.getBoundingClientRect();
    if (!r) return;
    const width = Math.min(340, window.innerWidth - 16);
    const left = Math.min(window.innerWidth - width - 8, Math.max(8, r.left - 12));
    const below = r.bottom + 8;
    const h = popRef.current?.offsetHeight || 160;
    const top = below + h > window.innerHeight - 8 ? Math.max(8, r.top - h - 8) : below;
    setPos({ left, top });
  };
  useLayoutEffect(() => {
    if (open) place();
  }, [open]);
  useEffect(() => {
    if (!open) return;
    const onDown = (e: MouseEvent) => {
      if (popRef.current?.contains(e.target as Node) || btnRef.current?.contains(e.target as Node)) return;
      setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setOpen(false);
        btnRef.current?.focus();
      }
    };
    const onScroll = () => place();
    document.addEventListener("mousedown", onDown);
    document.addEventListener("keydown", onKey);
    window.addEventListener("resize", onScroll);
    document.addEventListener("scroll", onScroll, true);
    return () => {
      document.removeEventListener("mousedown", onDown);
      document.removeEventListener("keydown", onKey);
      window.removeEventListener("resize", onScroll);
      document.removeEventListener("scroll", onScroll, true);
    };
  }, [open]);

  return (
    <>
      <button
        ref={btnRef}
        type="button"
        className="info"
        aria-label={label}
        aria-expanded={open}
        aria-controls={open ? id : undefined}
        onClick={(e) => {
          e.stopPropagation();
          setOpen((v) => !v);
        }}
        data-testid={testId}
      >
        i
      </button>
      {open &&
        createPortal(
          <div ref={popRef} id={id} role="dialog" aria-label={label} className="pop" style={{ left: pos.left, top: pos.top }}>
            {children}
          </div>,
          document.body,
        )}
    </>
  );
};

/* ---------- "How this was measured" drawer ---------- */
export const MethodDrawer: React.FC<{
  title?: string;
  triggerLabel?: string;
  children: React.ReactNode;
  testId?: string;
}> = ({ title = "How this was measured", triggerLabel = "How this was measured", children, testId }) => {
  const ref = useRef<HTMLDialogElement>(null);
  const titleId = useId();
  return (
    <>
      <button type="button" className="quiet-btn" onClick={() => ref.current?.showModal()} data-testid={testId}>
        {triggerLabel}
      </button>
      <dialog
        ref={ref}
        className="drawer"
        aria-labelledby={titleId}
        onClick={(e) => {
          if (e.target === ref.current) ref.current?.close();
        }}
      >
        <button type="button" className="icon-btn drawer-close" aria-label="Close" onClick={() => ref.current?.close()}>
          <Icon name="close" size={19} />
        </button>
        <h2 id={titleId}>{title}</h2>
        <div className="drawer-body">{children}</div>
      </dialog>
    </>
  );
};

/* ---------- Page scaffolding ---------- */
export const PageHead: React.FC<{ title: React.ReactNode; sub?: React.ReactNode; lede?: React.ReactNode; children?: React.ReactNode }> = ({
  title,
  sub,
  lede,
  children,
}) => (
  <header className="page-head">
    <h1>{title}</h1>
    {sub && <p className="sub">{sub}</p>}
    {lede && <p className="lede">{lede}</p>}
    {children}
  </header>
);

export const Section: React.FC<{
  id?: string;
  title: React.ReactNode;
  hint?: React.ReactNode;
  className?: string;
  children: React.ReactNode;
  testId?: string;
}> = ({ id, title, hint, className, children, testId }) => {
  const autoId = useId();
  const hId = id ? `${id}-h` : autoId;
  return (
    <section className={`section ${className || ""}`} aria-labelledby={hId} id={id} data-testid={testId}>
      <h2 id={hId}>{title}</h2>
      {hint && <p className="hint">{hint}</p>}
      {children}
    </section>
  );
};

export const LoadingLine: React.FC<{ children?: React.ReactNode }> = ({ children = "Loading…" }) => (
  <p role="status" className="loading-line">
    <span className="spin" aria-hidden="true" />
    {children}
  </p>
);

export const ErrorLine: React.FC<{ error: unknown; onRetry?: () => void }> = ({ error, onRetry }) => (
  <p role="alert" className="error-line">
    <Icon name="warning" size={18} />
    <span>{error instanceof Error ? error.message : String(error)}</span>
    {onRetry && (
      <button type="button" className="textlink" onClick={onRetry}>
        Try again
      </button>
    )}
  </p>
);

/** Bar with a quiet track, used for specialisation and rankings. */
export const BarTrack: React.FC<{ value: number; max: number; label?: string }> = ({ value, max, label }) => (
  <div className="bar-track" role={label ? "img" : undefined} aria-label={label}>
    <div className="bar" style={{ width: `${max > 0 ? Math.max(2, Math.min(100, (value / max) * 100)) : 0}%` }} />
  </div>
);

/** Copy an identifier without showing it in the page. */
export const CopyIdButton: React.FC<{ id: string; label?: string }> = ({ id, label = "Copy ID" }) => {
  const [done, setDone] = useState(false);
  return (
    <button
      type="button"
      className="quiet-btn"
      title={id}
      onClick={async () => {
        try {
          await navigator.clipboard.writeText(id);
          setDone(true);
          setTimeout(() => setDone(false), 1600);
        } catch {
          window.prompt("Copy this ID", id);
        }
      }}
    >
      <Icon name={done ? "check" : "copy"} size={16} />
      <span>{done ? "Copied" : label}</span>
    </button>
  );
};
