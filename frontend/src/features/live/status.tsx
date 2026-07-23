import { Fragment } from "react";
import {
  Activity, Check, CheckCircle2, CircleX, Flag, Hourglass, Loader2, Radio, SlidersHorizontal,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { LIFECYCLE_STEPS, PHASE_INDEX, type LivePhase } from "./lifecycle";
import type { LiveStatus } from "./use-live-session";

const STEP_ICONS: Record<LivePhase, typeof Activity> = {
  setup: SlidersHorizontal,
  ready: CheckCircle2,
  workout: Activity,
  completed: Flag,
};

/**
 * Workout lifecycle stepper — persistent, fixed height, communicates the
 * phase machine at a glance (done = ticked, current = filled, rest = muted).
 * Non-interactive by design: progression happens through the controls.
 */
export function LifecycleBar({ phase, className }: { phase: LivePhase; className?: string }) {
  const current = PHASE_INDEX[phase];
  return (
    <ol
      aria-label="Workout progress"
      className={cn("flex items-center rounded-xl border border-border/60 bg-card px-4 py-3", className)}
    >
      {LIFECYCLE_STEPS.map((step, i) => {
        const done = i < current;
        const active = i === current;
        const Icon = STEP_ICONS[step.id];
        return (
          <Fragment key={step.id}>
            <li aria-current={active ? "step" : undefined} className="flex min-w-0 items-center gap-2.5">
              <span
                className={cn(
                  "grid size-8 shrink-0 place-items-center rounded-full border transition-colors duration-300",
                  done && "border-primary/60 bg-primary/15 text-primary",
                  active && "border-primary bg-primary text-primary-foreground shadow-[0_0_0_4px_hsl(var(--primary)/.15)]",
                  !done && !active && "border-border bg-background text-muted-foreground",
                )}
              >
                {done
                  ? <Check className="size-4" />
                  : <Icon className={cn("size-4", active && phase === "workout" && "animate-pulse")} />}
              </span>
              <span className="hidden min-w-0 sm:block">
                <span
                  className={cn(
                    "block truncate text-xs font-semibold transition-colors",
                    active ? "text-foreground" : done ? "text-foreground/80" : "text-muted-foreground",
                  )}
                >
                  {step.label}
                </span>
                <span className="block truncate text-[11px] text-muted-foreground">{step.hint}</span>
              </span>
            </li>
            {i < LIFECYCLE_STEPS.length - 1 && (
              <span
                aria-hidden
                className={cn(
                  "mx-3 h-px min-w-3 flex-1 transition-colors duration-500",
                  i < current ? "bg-primary/60" : "bg-border",
                )}
              />
            )}
          </Fragment>
        );
      })}
    </ol>
  );
}

interface StatusMeta {
  label: string;
  icon: typeof Activity;
  variant: "outline" | "primary" | "success" | "warning" | "destructive";
  spin?: boolean;
  liveDot?: boolean;
}

/**
 * Icon + color status pill — replaces plain-text status. `ready` refines the
 * idle state ("Waiting for video" vs "Ready" once a source is chosen).
 */
export function StatusPill({ status, ready }: { status: LiveStatus; ready: boolean }) {
  const meta: StatusMeta =
    status === "idle"
      ? ready
        ? { label: "Ready", icon: CheckCircle2, variant: "primary" }
        : { label: "Waiting for video", icon: Hourglass, variant: "outline" }
      : status === "connecting"
        ? { label: "Connecting…", icon: Loader2, variant: "warning", spin: true }
        : status === "live"
          ? { label: "Live", icon: Radio, variant: "destructive", liveDot: true }
          : status === "ended"
            ? { label: "Completed", icon: Flag, variant: "success" }
            : { label: "Error", icon: CircleX, variant: "destructive" };
  const Icon = meta.icon;
  return (
    <Badge variant={meta.variant} className="gap-1.5 px-3 py-1">
      {meta.liveDot && <span className="size-1.5 animate-pulse rounded-full bg-destructive" />}
      <Icon className={cn("size-3.5", meta.spin && "animate-spin")} />
      {meta.label}
    </Badge>
  );
}
