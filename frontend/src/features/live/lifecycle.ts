import type { LiveStatus } from "./use-live-session";

/**
 * Pure workout-lifecycle model — no React, no IO.
 *
 * The Live page is a state machine:
 *
 *   Set up ──(source chosen)──▶ Ready ──(Start)──▶ Workout ──(end)──▶ Completed
 *                                                              │
 *                                                       (optional: View report)
 *
 * `derivePhase` is exported pure so transitions are trivially testable.
 */
export type LivePhase = "setup" | "ready" | "workout" | "completed";

/**
 * Map (stream status, input readiness) onto the user-facing phase.
 * A stream error keeps the "workout" phase highlighted — that is where the
 * failure happened; the status pill carries the actual "Error" indicator.
 */
export function derivePhase(status: LiveStatus, ready: boolean): LivePhase {
  switch (status) {
    case "ended":
      return "completed";
    case "connecting":
    case "live":
    case "error":
      return "workout";
    default:
      return ready ? "ready" : "setup";
  }
}

export interface LifecycleStep {
  id: LivePhase;
  label: string;
  hint: string;
}

/** Ordered steps rendered by the stepper (index = progress). */
export const LIFECYCLE_STEPS: LifecycleStep[] = [
  { id: "setup", label: "Set up", hint: "Choose a video source" },
  { id: "ready", label: "Ready", hint: "Start when you are" },
  { id: "workout", label: "Workout", hint: "Live coaching" },
  { id: "completed", label: "Complete", hint: "Review results" },
];

export const PHASE_INDEX: Record<LivePhase, number> = {
  setup: 0,
  ready: 1,
  workout: 2,
  completed: 3,
};
