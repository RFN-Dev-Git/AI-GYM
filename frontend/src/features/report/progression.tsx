import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip as ChartTooltip, XAxis, YAxis } from "recharts";
import type { Repetition } from "@/schemas";
import { formatSeconds } from "@/lib/format";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { buildProgression, scoreAxisDomain } from "./insights";

interface DotProps {
  cx?: number;
  cy?: number;
  payload?: { good: boolean };
}

/** Verdict-colored point — same green/red language the old bars used. */
function VerdictDot({ cx = 0, cy = 0, payload }: DotProps) {
  return (
    <circle
      cx={cx}
      cy={cy}
      r={4}
      fill={payload?.good ? "hsl(var(--success))" : "hsl(var(--destructive))"}
      stroke="hsl(var(--card))"
      strokeWidth={1.5}
    />
  );
}

interface TooltipEntry {
  payload?: { rep: number; score: number; good: boolean; duration: number | null; failed: number };
}

function ScoreTooltip({ active, payload }: { active?: boolean; payload?: TooltipEntry[] }) {
  const p = payload?.[0]?.payload;
  if (!active || !p) return null;
  return (
    <div
      className="text-xs"
      style={{ background: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: 12, padding: "8px 12px" }}
    >
      <p className="font-semibold">
        Rep {p.rep} ·{" "}
        <span className={p.good ? "text-success" : "text-destructive"}>{p.good ? "GOOD" : "BAD"}</span>
      </p>
      <p className="mt-0.5 text-muted-foreground">
        Score <span className="font-bold text-foreground">{p.score}</span> · {formatSeconds(p.duration)}
        {p.failed > 0 && <span className="text-destructive"> · {p.failed} failed check{p.failed === 1 ? "" : "s"}</span>}
      </p>
    </div>
  );
}

/**
 * Score per repetition, as a **line plot** — the old bar-chart card kept
 * verbatim (same slot, height, axes, colors), only the marks changed: a
 * lime monotone line with green/red verdict dots. A line reads progression
 * (fatigue, warm-up, breakdown) better than isolated bars.
 *
 * The Y-axis domain comes from `scoreAxisDomain` (data-fitted, padded,
 * 20-point minimum window) instead of a flat [0, 100], so small rep-to-rep
 * changes stay readable without zooming into noise or clipping outliers.
 */
export function ScoreProgression({ history }: { history: Repetition[] }) {
  const { points } = buildProgression(history);
  const domain = scoreAxisDomain(points.map((p) => p.score));

  return (
    <Card className="lg:col-span-2">
      <CardHeader>
        <CardTitle>Score per repetition</CardTitle>
        <CardDescription>Dots: green = classified good at runtime, red = bad</CardDescription>
      </CardHeader>
      <CardContent className="h-56">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={points} margin={{ top: 4, right: 8, bottom: 0, left: -18 }}>
            <CartesianGrid vertical={false} stroke="hsl(var(--border))" strokeDasharray="3 3" />
            <XAxis
              dataKey="rep"
              tick={{ fontSize: 11 }}
              stroke="hsl(var(--muted-foreground))"
              tickLine={false}
              axisLine={false}
              tickFormatter={(v: number) => `#${v}`}
            />
            <YAxis domain={domain} tick={{ fontSize: 11 }} stroke="hsl(var(--muted-foreground))" tickLine={false} axisLine={false} />
            <ChartTooltip content={<ScoreTooltip />} cursor={{ stroke: "hsl(var(--border))" }} />
            <Line
              type="monotone"
              dataKey="score"
              stroke="hsl(var(--primary))"
              strokeWidth={2.5}
              dot={<VerdictDot />}
              activeDot={{ r: 5, strokeWidth: 2, stroke: "hsl(var(--card))" }}
            />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
