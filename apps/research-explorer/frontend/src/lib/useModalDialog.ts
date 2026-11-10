import { RefObject, useEffect, useRef } from "react";

const FOCUSABLE_SELECTOR = [
  "a[href]",
  "button:not([disabled])",
  "input:not([disabled]):not([type='hidden'])",
  "select:not([disabled])",
  "textarea:not([disabled])",
  "summary",
  "[tabindex]:not([tabindex='-1'])",
].join(", ");

function getFocusableElements(container: HTMLElement): HTMLElement[] {
  const candidates = Array.from(
    container.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR)
  );
  return candidates.filter((el) => {
    if (el.hasAttribute("disabled") || el.getAttribute("aria-hidden") === "true") {
      return false;
    }
    const closedDetails = el.closest("details:not([open])");
    if (closedDetails && el.tagName !== "SUMMARY") {
      return false;
    }
    const style = window.getComputedStyle(el);
    if (style.display === "none" || style.visibility === "hidden") {
      return false;
    }
    return true;
  });
}

export interface UseModalDialogOptions {
  isOpen: boolean;
  onClose: () => void;
  initialFocusRef?: RefObject<HTMLElement | null>;
}

export function useModalDialog(
  optionsOrIsOpen: UseModalDialogOptions | boolean,
  onCloseArg?: () => void,
  initialFocusRefArg?: RefObject<HTMLElement | null>
): RefObject<HTMLDivElement> {
  const isOptions = typeof optionsOrIsOpen === "object";
  const isOpen = isOptions ? optionsOrIsOpen.isOpen : optionsOrIsOpen;
  const onClose = isOptions ? optionsOrIsOpen.onClose : onCloseArg!;
  const initialFocusRef = isOptions
    ? optionsOrIsOpen.initialFocusRef
    : initialFocusRefArg;

  const dialogRef = useRef<HTMLDivElement>(null!);
  const openerRef = useRef<HTMLElement | null>(null);
  const onCloseRef = useRef(onClose);
  onCloseRef.current = onClose;

  useEffect(() => {
    if (!isOpen) return;

    openerRef.current = document.activeElement as HTMLElement | null;

    const focusTimer = window.setTimeout(() => {
      if (initialFocusRef?.current) {
        initialFocusRef.current.focus();
        return;
      }
      if (dialogRef.current) {
        const focusables = getFocusableElements(dialogRef.current);
        if (focusables.length > 0) {
          focusables[0].focus();
        } else {
          dialogRef.current.focus();
        }
      }
    }, 15);

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.defaultPrevented) return;

      if (e.key === "Escape") {
        if (dialogRef.current?.querySelector('[data-picker-open="true"]')) {
          return;
        }
        e.preventDefault();
        e.stopPropagation();
        onCloseRef.current();
        return;
      }

      if (e.key === "Tab" && dialogRef.current) {
        const focusables = getFocusableElements(dialogRef.current);
        if (focusables.length === 0) {
          e.preventDefault();
          return;
        }
        const first = focusables[0];
        const last = focusables[focusables.length - 1];
        const active = document.activeElement as HTMLElement | null;

        if (e.shiftKey) {
          if (!active || active === first || !dialogRef.current.contains(active)) {
            e.preventDefault();
            last.focus();
          }
        } else {
          if (!active || active === last || !dialogRef.current.contains(active)) {
            e.preventDefault();
            first.focus();
          }
        }
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => {
      window.clearTimeout(focusTimer);
      document.removeEventListener("keydown", handleKeyDown);
      const opener = openerRef.current;
      if (opener && typeof opener.focus === "function" && document.body.contains(opener)) {
        window.setTimeout(() => opener.focus(), 0);
      }
    };
  }, [isOpen, initialFocusRef]);

  return dialogRef;
}
