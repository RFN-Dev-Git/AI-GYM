import { CheckCircle2, Lightbulb, ShieldCheck, TrendingUp } from "lucide-react";
import type { RuleDefinition, RuleStats, SessionSummary } from "@/schemas";
import { cn } from "@/lib/utils";
import { titleCase } from "@/lib/format";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { buildCoaching, formatMeasured } from "./insights";
import { RangeGauge } from "./range-gauge";

/**
 * Coaching insights — the "what now" of the report.
 *
 * Unifies the old mistakes card and rule-statistics card into one prioritized
 * coaching list: every failing rule gets its failure rate, a visual
 * measurement-vs-target gauge, and an actionable recommendation.
 */
export function CoachingPanel({
  rules,
  stats,
  summary,
}: {
  rules: RuleDefinition[];
  stats: RuleStats[] | null | undefined;
  summary: SessionSummary;
}) {
  const model = buildCoaching(rules, stats, summary.common_errors);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <TrendingUp className="size-4 text-primary" /> Coaching insights
        </CardTitle>
        <CardDescription>
          {model.items.length === 0
            ? "Nothing to correct — every check passed"
            : "What to correct, in priority order"}
          {!model.fromStats && model.items.length > 0 && " · older export: counts only"}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {model.items.length === 0 ? (
          <p className="flex items-center justify-center gap-2 py-8 text-sm font-medium text-success">
            <ShieldCheck className="size-5" /> Perfect session — no form issues detected.
          </p>
        ) : (
          model.items.map((item) => {
            const def = item.def;
            const priority = def?.severity === "error";
            return (
              <article
                key={item.name}
                className={cn(
                  "space-y-3 rounded-xl border p-4",
                  priority ? "border-destructive/40 bg-destructive/5" : "border-warning/40 bg-warning/5",
                )}
              >
                <header className="flex flex-wrap items-center gap-2">
                  <Badge variant={priority ? "destructive" : "warning"}>
                    {priority ? "Priority fix" : "Refine"}
                  </Badge>
                  <h4 className="text-sm font-semibold">{titleCase(item.name)}</h4>
                  <span className="text-xs text-muted-foreground">
                    failed in {item.failed}
                    {item.evaluations != null ? ` of ${item.evaluations}` : ""} rep
                    {(item.evaluations ?? item.failed) === 1 ? "" : "s"}
                    {item.successRate != null && ` · ${item.successRate.toFixed(0)}% pass rate`}
                  </span>
                </header>

                {def?.message && <p className="text-xs text-muted-foreground">Coach cue: “{def.message}”</p>}

                {def && (
                  <div className="grid items-center gap-3 sm:grid-cols-[1fr_auto]">
                    <RangeGauge
                      min={def.expected_min}
                      max={def.expected_max}
                      value={item.avgMeasured}
                      unit={def.value_unit}
                    />
                    <p className="text-right text-xs text-muted-foreground sm:w-24 sm:text-right">
                      your avg{" "}
                      <span className={cn("font-bold", item.avgMeasured != null ? "text-foreground" : "")}>
                        {formatMeasured(item.avgMeasured, def.value_unit)}
                      </span>
                    </p>
                  </div>
                )}

                <p className="flex items-start gap-2 text-sm">
                  <Lightbulb className="mt-0.5 size-4 shrink-0 text-warning" />
                  <span>{item.tip}</span>
                </p>
              </article>
            );
          })
        )}

        {model.passing.length > 0 && (
          <footer className="flex flex-wrap items-center gap-1.5 border-t border-border/60 pt-3">
            <span className="flex items-center gap-1 text-xs font-medium text-muted-foreground">
              <CheckCircle2 className="size-3.5 text-success" /> Passing every rep:
            </span>
            {model.passing.map((name) => (
              <Badge key={name} variant="success">
                {titleCase(name)}
              </Badge>
            ))}
          </footer>
        )}
      </CardContent>
    </Card>
  );
}
