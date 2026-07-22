import { cn } from "@/lib/utils";
import { formatMeasured, gaugeGeometry, rangeText } from "./insights";

/**
 * Visual measurement indicator — shows where a measured value sits relative
 * to its expected range: the green zone is "expected", ticks mark the bounds,
 * and the dot is the measurement (colored by in/out of range).
 */
export function RangeGauge({
  min,
  max,
  value,
  unit,
  className,
}: {
  min: number | null | undefined;
  max: number | null | undefined;
  value: number | null | undefined;
  unit: string | null | undefined;
  className?: string;
}) {
  const g = gaugeGeometry(min, max, value);
  if (!g) return null;
  const lo = g.loPct ?? 0;
  const hi = g.hiPct ?? 100;
  return (
    <div className={cn("w-full", className)}>
      <div className="relative h-2 rounded-full bg-muted">
        {/* expected zone */}
        <div
          className="absolute inset-y-0 rounded-full bg-success/25"
          style={{ left: `${lo}%`, width: `${Math.max(2, hi - lo)}%` }}
        />
        {/* bound ticks */}
        {g.loPct != null && (
          <span className="absolute -top-0.5 h-3 w-0.5 rounded bg-success" style={{ left: `calc(${g.loPct}% - 1px)` }} />
        )}
        {g.hiPct != null && (
          <span className="absolute -top-0.5 h-3 w-0.5 rounded bg-success" style={{ left: `calc(${g.hiPct}% - 1px)` }} />
        )}
        {/* measured marker */}
        {g.posPct != null && (
          <span
            className={cn(
              "absolute top-1/2 size-3 -translate-x-1/2 -translate-y-1/2 rounded-full ring-2 ring-card",
              g.inRange ? "bg-success" : "bg-destructive",
            )}
            style={{ left: `${g.posPct}%` }}
          />
        )}
      </div>
      <div className="mt-1.5 flex items-center justify-between text-[10px] font-medium tabular-nums text-muted-foreground">
        <span>{formatMeasured(g.domainMin, unit)}</span>
        <span className="text-success/90">target {rangeText(min, max, unit)}</span>
        <span>{formatMeasured(g.domainMax, unit)}</span>
      </div>
    </div>
  );
}
