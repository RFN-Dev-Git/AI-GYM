import { Fragment, useState } from "react";
import { motion } from "framer-motion";
import { CheckCircle2, ChevronDown, Info, Lightbulb, XCircle } from "lucide-react";
import type { Repetition, RuleDefinition } from "@/schemas";
import { cn } from "@/lib/utils";
import { formatSeconds, scoreColor, titleCase } from "@/lib/format";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { formatMeasured, recommendationFor } from "./insights";
import { RangeGauge } from "./range-gauge";

const JUDGED_BY_INFO: Record<string, string> = {
  completion: "Counted as a completed rep. This counter does not judge quality — the score carries form feedback.",
  rules: "Marked bad because failing form rules forced the verdict.",
  counter: "Quality judged by the counter itself (range-of-motion / tempo / accumulated violations).",
};

function JudgedByBadge({ value }: { value: string }) {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Badge variant="outline" className="gap-1">
          <Info className="size-3" />
          {titleCase(value)}
        </Badge>
      </TooltipTrigger>
      <TooltipContent>{JUDGED_BY_INFO[value] ?? value}</TooltipContent>
    </Tooltip>
  );
}

/** One evaluation row: verdict, measured value, gauge, and a fix when failed. */
function EvaluationRow({ rep, def }: { rep: Repetition["evaluations"][number]; def: RuleDefinition | undefined }) {
  return (
    <div
      className={cn(
        "space-y-2 rounded-lg border p-3",
        rep.passed ? "border-border/50" : "border-destructive/40 bg-destructive/5",
      )}
    >
      <div className="flex flex-wrap items-center gap-2">
        {rep.passed ? (
          <span className="flex items-center gap-1.5 text-sm font-medium text-success">
            <CheckCircle2 className="size-4" /> {titleCase(rep.rule)}
          </span>
        ) : (
          <span className="flex items-center gap-1.5 text-sm font-medium text-destructive">
            <XCircle className="size-4" /> {titleCase(rep.rule)}
          </span>
        )}
        {def && <Badge variant={def.severity === "error" ? "destructive" : def.severity === "warning" ? "warning" : "default"}>{def.severity}</Badge>}
        <span className="ml-auto text-sm tabular-nums">
          measured{" "}
          <strong className={rep.passed ? "text-foreground" : "text-destructive"}>
            {formatMeasured(rep.measured_value, def?.value_unit)}
          </strong>
        </span>
      </div>

      {def && (def.expected_min != null || def.expected_max != null) && (
        <RangeGauge min={def.expected_min} max={def.expected_max} value={rep.measured_value} unit={def.value_unit} />
      )}
      {def && def.expected_min == null && def.expected_max == null && def.message && (
        <p className="text-xs text-muted-foreground">“{def.message}”</p>
      )}

      {!rep.passed && def && (
        <p className="flex items-start gap-1.5 text-xs text-muted-foreground">
          <Lightbulb className="mt-0.5 size-3.5 shrink-0 text-warning" />
          {recommendationFor(def, rep.measured_value)}
        </p>
      )}
    </div>
  );
}

/**
 * Repetition history — expandable rows; each failed check shows its measured
 * value on a target gauge plus the concrete fix.
 */
export function RepList({ history, rules }: { history: Repetition[]; rules: RuleDefinition[] }) {
  const [openReps, setOpenReps] = useState<Set<number>>(new Set());
  const defs = new Map(rules.map((r) => [r.name, r]));

  const toggleRep = (n: number) =>
    setOpenReps((cur) => {
      const next = new Set(cur);
      if (next.has(n)) next.delete(n);
      else next.add(n);
      return next;
    });

  return (
    <Card>
      <CardHeader>
        <CardTitle>Repetition breakdown</CardTitle>
        <CardDescription>Click a rep for the full check-by-check detail</CardDescription>
      </CardHeader>
      <CardContent className="space-y-2">
        {history.map((rep) => {
          const failed = rep.evaluations.filter((e) => !e.passed);
          const open = openReps.has(rep.number);
          return (
            <Fragment key={rep.number}>
              <button
                onClick={() => toggleRep(rep.number)}
                aria-expanded={open}
                className={cn(
                  "flex w-full items-center gap-3 rounded-xl border px-4 py-3 text-left transition-colors",
                  rep.good
                    ? "border-border/60 bg-card hover:border-success/40"
                    : "border-destructive/40 bg-destructive/5 hover:border-destructive/60",
                )}
              >
                <span className="w-8 shrink-0 text-sm font-bold tabular-nums text-muted-foreground">#{rep.number}</span>
                <Badge variant={rep.good ? "success" : "destructive"}>{rep.good ? "GOOD" : "BAD"}</Badge>
                <JudgedByBadge value={rep.judged_by} />
                <span className="ml-auto hidden text-xs text-muted-foreground sm:block">
                  {formatSeconds(rep.duration_seconds)} · {failed.length ? `${failed.length} failed` : "all passed"}
                </span>
                <span className={cn("text-sm font-bold tabular-nums", scoreColor(rep.score))}>{rep.score.toFixed(0)}</span>
                <ChevronDown className={cn("size-4 shrink-0 text-muted-foreground transition-transform", open && "rotate-180")} />
              </button>
              {open && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  className="overflow-hidden pl-4"
                >
                  <div className="space-y-3 rounded-xl border border-border/60 bg-card/60 p-4">
                    <div className="flex flex-wrap gap-4 text-xs text-muted-foreground">
                      <span>
                        Frames <strong className="text-foreground">{rep.start_frame ?? "—"} → {rep.end_frame ?? "—"}</strong>
                      </span>
                      <span>
                        Duration <strong className="text-foreground">{formatSeconds(rep.duration_seconds)}</strong>
                      </span>
                      <span>
                        Checks <strong className="text-foreground">{rep.evaluations.length}</strong>
                      </span>
                      <span>
                        Failed{" "}
                        <strong className={failed.length ? "text-destructive" : "text-foreground"}>{failed.length}</strong>
                      </span>
                    </div>
                    {rep.evaluations.map((ev) => (
                      <EvaluationRow key={ev.rule} rep={ev} def={defs.get(ev.rule)} />
                    ))}
                  </div>
                </motion.div>
              )}
            </Fragment>
          );
        })}
      </CardContent>
    </Card>
  );
}
