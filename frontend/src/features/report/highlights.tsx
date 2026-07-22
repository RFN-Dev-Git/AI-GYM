import { AlertTriangle, CheckCircle2, Lightbulb, ThumbsDown, Trophy } from "lucide-react";
import type { Repetition, RuleDefinition } from "@/schemas";
import { cn } from "@/lib/utils";
import { formatSeconds, scoreColor, titleCase } from "@/lib/format";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { pickBestWorst, recommendationFor } from "./insights";

function HighlightCard({
  rep,
  kind,
  delta,
  rules,
}: {
  rep: Repetition;
  kind: "best" | "worst";
  delta: number;
  rules: Map<string, RuleDefinition>;
}) {
  const best = kind === "best";
  const failed = rep.evaluations.filter((e) => !e.passed);
  const firstTip = failed
    .map((e) => rules.get(e.rule))
    .find((d): d is RuleDefinition => Boolean(d));
  return (
    <div
      className={cn(
        "rounded-xl border p-4",
        best ? "border-success/40 bg-success/5" : "border-destructive/40 bg-destructive/5",
      )}
    >
      <div className="flex items-center justify-between gap-3">
        <p className="flex items-center gap-2 text-sm font-semibold">
          {best ? <Trophy className="size-4 text-success" /> : <ThumbsDown className="size-4 text-destructive" />}
          {best ? "Best repetition" : "Worst repetition"} · #{rep.number}
        </p>
        <span className={cn("text-2xl font-bold tabular-nums", scoreColor(rep.score))}>{rep.score.toFixed(0)}</span>
      </div>

      <p className="mt-1.5 text-xs text-muted-foreground">
        {formatSeconds(rep.duration_seconds)}
        {" · "}
        <span className={delta >= 0 ? "text-success" : "text-destructive"}>
          {delta >= 0 ? "+" : ""}
          {delta.toFixed(0)} pts
        </span>{" "}
        vs session average
      </p>

      <div className="mt-3 space-y-2">
        {failed.length === 0 ? (
          <p className="flex items-center gap-1.5 text-sm text-success">
            <CheckCircle2 className="size-4" /> Clean rep — all {rep.evaluations.length} checks passed.
          </p>
        ) : (
          <>
            <div className="flex flex-wrap gap-1.5">
              {failed.map((e) => (
                <Badge key={e.rule} variant="destructive">
                  <AlertTriangle className="size-3" /> {titleCase(e.rule)}
                </Badge>
              ))}
            </div>
            {firstTip && (
              <p className="flex items-start gap-1.5 text-xs text-muted-foreground">
                <Lightbulb className="mt-0.5 size-3.5 shrink-0 text-warning" />
                {recommendationFor(firstTip, failed.find((f) => f.rule === firstTip.name)?.measured_value)}
              </p>
            )}
          </>
        )}
      </div>
    </div>
  );
}

/**
 * Best / worst repetition summary — the two extremes side by side, with the
 * reason each earned its score (checks passed / failed + what to fix).
 */
export function RepHighlights({
  history,
  rules,
}: {
  history: Repetition[];
  rules: RuleDefinition[];
}) {
  const model = pickBestWorst(history);
  if (!model) return null;
  const defs = new Map(rules.map((r) => [r.name, r]));

  return (
    <Card>
      <CardHeader>
        <CardTitle>Repetition highlights</CardTitle>
        <CardDescription>
          {model.single ? "Your only rep this session" : "Best and worst of the session — and why"}
        </CardDescription>
      </CardHeader>
      <CardContent className={cn("grid gap-3", !model.single && "sm:grid-cols-2")}>
        <HighlightCard rep={model.best} kind="best" delta={model.best.score - model.average} rules={defs} />
        {!model.single && (
          <HighlightCard rep={model.worst} kind="worst" delta={model.worst.score - model.average} rules={defs} />
        )}
      </CardContent>
    </Card>
  );
}
