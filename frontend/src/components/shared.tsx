import type * as React from "react";
import { cn } from "@/lib/utils";
import { scoreColor } from "@/lib/format";

/** Centered empty state — icon, title, hint, optional action. */
export function EmptyState({
  icon: Icon,
  title,
  hint,
  action,
  className,
}: {
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  hint?: string;
  action?: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("flex flex-col items-center justify-center gap-3 py-16 text-center", className)}>
      <div className="rounded-2xl border border-border bg-card p-4">
        <Icon className="size-6 text-muted-foreground" />
      </div>
      <p className="text-sm font-medium">{title}</p>
      {hint && <p className="max-w-xs text-xs text-muted-foreground">{hint}</p>}
      {action}
    </div>
  );
}

/** Big dashboard/history stat: label + value + optional icon accent. */
export function StatCard({
  label,
  value,
  hint,
  icon: Icon,
  className,
  valueClassName,
}: {
  label: string;
  value: React.ReactNode;
  hint?: string;
  icon?: React.ComponentType<{ className?: string }>;
  className?: string;
  valueClassName?: string;
}) {
  return (
    <div className={cn("rounded-xl border border-border/60 bg-card p-4", className)}>
      <div className="flex items-center justify-between">
        <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">{label}</p>
        {Icon && <Icon className="size-4 text-primary" />}
      </div>
      <p className={cn("mt-2 text-2xl font-bold tabular-nums", valueClassName)}>{value}</p>
      {hint && <p className="mt-1 text-xs text-muted-foreground">{hint}</p>}
    </div>
  );
}

/** Circular score gauge with an arc (no chart library needed). */
export function ScoreRing({ score, size = 148, label = "Score" }: { score: number | null; size?: number; label?: string }) {
  const value = Math.max(0, Math.min(100, score ?? 0));
  const stroke = 10;
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  return (
    <div className="relative inline-block" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" strokeWidth={stroke} className="stroke-muted" />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={c}
          strokeDashoffset={c * (1 - value / 100)}
          className={cn("transition-[stroke-dashoffset] duration-700", {
            "stroke-success": value >= 80,
            "stroke-warning": value >= 50 && value < 80,
            "stroke-destructive": value < 50,
          })}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className={cn("text-4xl font-bold tabular-nums", scoreColor(score))}>
          {score == null ? "—" : Math.round(score)}
        </span>
        <span className="text-xs font-medium uppercase tracking-widest text-muted-foreground">{label}</span>
      </div>
    </div>
  );
}
