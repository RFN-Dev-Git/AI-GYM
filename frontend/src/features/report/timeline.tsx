import type { Repetition } from "@/schemas";
import { cn } from "@/lib/utils";
import { formatClock, formatSeconds, titleCase } from "@/lib/format";
import { buildTimeline } from "./insights";

/**
 * Rep timeline — a slim interactive strip living inside the Repetition
 * history card (no card chrome of its own). Segments are proportional to
 * rep duration, hatched-free gaps read as rest, failing reps carry an
 * error bubble, and clicking a segment toggles that rep's breakdown.
 * Silently omitted for exports without frame timing.
 */
export function RepTimeline({
  history,
  fps,
  totalDuration,
  openReps,
  onToggle,
  className,
}: {
  history: Repetition[];
  fps: number | null | undefined;
  totalDuration: number | null | undefined;
  openReps: Set<number>;
  onToggle: (repNumber: number) => void;
  className?: string;
}) {
  const model = buildTimeline(history, fps, totalDuration);
  if (!model) return null;

  return (
    <div className={cn("space-y-1.5", className)}>
      <div className="flex items-center justify-between text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
        <span>Timeline · green = good, red = failed checks</span>
        <span className="tabular-nums normal-case tracking-normal">{formatClock(model.duration)}</span>
      </div>
      <div className="flex h-8 items-stretch gap-px">
        {model.segments.map((seg, i) => {
          const grow = Math.max(seg.span, seg.kind === "gap" ? 0.004 : 0.01);
          if (seg.kind === "gap") {
            return <div key={`gap-${i}`} style={{ flexGrow: grow, flexBasis: 0 }} className="rounded-sm bg-muted/40" />;
          }
          const rep = seg.rep!;
          const failed = rep.evaluations.filter((e) => !e.passed);
          return (
            <button
              key={`rep-${rep.number}`}
              type="button"
              onClick={() => onToggle(rep.number)}
              aria-pressed={openReps.has(rep.number)}
              title={`Rep ${rep.number} · ${rep.good ? "GOOD" : "BAD"} · score ${rep.score.toFixed(0)} · ${formatClock(seg.start)}–${formatClock(seg.end)} · ${formatSeconds(rep.duration_seconds)}${
                failed.length ? `\nFailed: ${failed.map((f) => titleCase(f.rule)).join(", ")}` : ""
              }`}
              style={{ flexGrow: grow, flexBasis: 0 }}
              className={cn(
                "relative min-w-1.5 cursor-pointer rounded transition-all",
                rep.good ? "bg-success/70 hover:bg-success" : "bg-destructive/70 hover:bg-destructive",
                openReps.has(rep.number) && "ring-2 ring-ring ring-offset-1 ring-offset-card",
              )}
            >
              {failed.length > 0 && (
                <span className="absolute -top-1 right-0 grid size-3.5 place-items-center rounded-full bg-destructive text-[8px] font-bold text-white ring-1 ring-card">
                  {failed.length}
                </span>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}
