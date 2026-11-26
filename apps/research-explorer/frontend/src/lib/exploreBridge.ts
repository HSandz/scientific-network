/**
 * Hand-off from other pages (Network's release analysis, search) to the Explore graph:
 * the request is queued here, the app navigates to /explore, and the Explore page runs it
 * once its graph controller is mounted.
 */
export interface FocusRequest {
  nodeId: string;
  name?: string;
  /** Replace the canvas with the node's neighborhood (true) or append it (false). */
  replace: boolean;
}

let pending: FocusRequest | null = null;

export function queueExploreFocus(req: FocusRequest): void {
  pending = req;
}

export function takeExploreFocus(): FocusRequest | null {
  const r = pending;
  pending = null;
  return r;
}

type FocusHandler = (nodeId: string, name?: string) => void;
let handler: FocusHandler | null = null;

/** The mounted Explore page registers how to focus a node in its graph. */
export function registerExploreFocusHandler(h: FocusHandler | null): void {
  handler = h;
}

export function exploreFocusHandler(): FocusHandler | null {
  return handler;
}
