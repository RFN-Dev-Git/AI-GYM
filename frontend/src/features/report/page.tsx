import { Fragment, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { motion } from "framer-motion";
import {
  ArrowLeft, CheckCircle2, ChevronDown, FileJson, FileWarning, Gauge, Info, Lightbulb, Target, Timer, XCircle,
} from "lucide-react";
import { downloadSessionReport, useSession } from "@/lib/api/sessions";
import type { Repetition, RuleDefinition, RuleStats, SessionReport } from "@/schemas";
import { cn } from "@/lib/utils";
import { formatDate, formatSeconds, scoreColor, titleCase } from "@/lib/format";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { EmptyState, ScoreRing, StatCard } from "@/components/shared";
import { useToast } from "@/providers/toast";
import { avgTargetText, pickBestWorst, scoreRating, tipShortFor } from "./insights";
import { RangeGauge } from "./range-gauge";
import { RepTimeline } from "./timeline";
import { ScoreProgression } from "./progression";

const JUDGED_BY_INFO: Record<string, string> = {
  completion: "Counted as a completed rep. This counter does not judge quality — the score carries form feedback.",
  rules: "Marked bad because failing form rules forced the verdict.",
  counter: "Quality judged by the counter itself (range-of-motion / tempo / accumulated violations).",
};

function JudgedByBadge({ value }: { value: string }) {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Badge variant="outline" className="gap-1"><Info className="size-3" />{titleCase(value)}</Badge>
      </TooltipTrigger>
      <TooltipContent>{JUDGED_BY_INFO[value] ?? value}</TooltipContent>
    </Tooltip>
  );
}

function severityVariant(severity: string) {
  return severity === "error" ? "destructive" : severity === "warning" ? "warning" : "default";
}

/** Best/worst footnote cell: score + rep number, tooltip explains *why*. */
function ExtremesCell({ rep, kind }: { rep: Repetition; kind: "best" | "worst" }) {
  const best = kind === "best";
  const failed = rep.evaluations.filter((e) => !e.passed);
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <div className="cursor-default">
          <p className={cn("text-lg font-bold tabular-nums", best ? "text-success" : "text-warning")}>
            {rep.score.toFixed(0)}
          </p>
          <p className="text-[11px] text-muted-foreground">
            {best ? "Best" : "Worst"} rep · #{rep.number}
          </p>
        </div>
      </TooltipTrigger>
      <TooltipContent>
        {failed.length === 0
          ? `Clean rep — all ${rep.evaluations.length} checks passed (${formatSeconds(rep.duration_seconds)})`
          : `Failed: ${failed.map((f) => titleCase(f.rule)).join(", ")} (${formatSeconds(rep.duration_seconds)})`}
      </TooltipContent>
    </Tooltip>
  );
}

function RuleEvaluations({ rep, rules }: { rep: Repetition; rules: RuleDefinition[] }) {
  const defs = new Map(rules.map((r) => [r.name, r]));
  return (
    <div className="mt-3 overflow-hidden rounded-lg border border-border/60">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-muted/40 text-left text-[11px] uppercase tracking-wider text-muted-foreground">
            <th className="px-3 py-2 font-medium">Check</th>
            <th className="px-3 py-2 font-medium">Result</th>
            <th className="px-3 py-2 font-medium">Measured</th>
            <th className="px-3 py-2 font-medium">Expected</th>
            <th className="hidden px-3 py-2 font-medium md:table-cell">Message</th>
          </tr>
        </thead>
        <tbody>
          {rep.evaluations.map((ev) => {
            const def = defs.get(ev.rule);
            const expected =
              def?.expected_min != null || def?.expected_max != null
                ? `${def?.expected_min ?? "—"} – ${def?.expected_max ?? "—"}${def?.value_unit === "degrees" ? "°" : ""}`
                : "—";
            return (
              <tr key={ev.rule} className="border-t border-border/50 align-top">
                <td className="px-3 py-2">
                  <span className="font-medium">{titleCase(ev.rule)}</span>
                  {def && <Badge variant={severityVariant(def.severity)} className="ml-2">{def.severity}</Badge>}
                </td>
                <td className="px-3 py-2">
                  {ev.passed
                    ? <span className="inline-flex items-center gap-1 text-success"><CheckCircle2 className="size-4" />Pass</span>
                    : <span className="inline-flex items-center gap-1 text-destructive"><XCircle className="size-4" />Fail</span>}
                </td>
                {/* Measured: number + where it sits against the target range */}
                <td className="px-3 py-2">
                  <span className="tabular-nums">{ev.measured_value != null ? ev.measured_value.toFixed(1) : "—"}</span>
                  {def && (def.expected_min != null || def.expected_max != null) && (
                    <RangeGauge
                      className="mt-1.5 w-36 max-w-full"
                      min={def.expected_min}
                      max={def.expected_max}
                      value={ev.measured_value}
                      unit={def.value_unit}
                    />
                  )}
                </td>
                <td className="px-3 py-2 tabular-nums text-muted-foreground">{expected}</td>
                <td className="hidden max-w-xs px-3 py-2 text-xs text-muted-foreground md:table-cell">
                  <span className="line-clamp-2">{ev.message ?? def?.message ?? "—"}</span>
                  {!ev.passed && def && (
                    <span className="mt-1 flex items-start gap-1 text-foreground/80">
                      <Lightbulb className="mt-0.5 size-3.5 shrink-0 text-warning" />
                      {tipShortFor(def)}
                    </span>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export function ReportPage() {
  const { sessionId } = useParams();
  const { data: report, isLoading, isError, error } = useSession(sessionId);
  const { push } = useToast();
  const [openReps, setOpenReps] = useState<Set<number>>(new Set());
  const [downloading, setDownloading] = useState(false);

  if (isLoading) {
    return <div className="space-y-4"><Skeleton className="h-8 w-64" /><Skeleton className="h-40" /><Skeleton className="h-64" /></div>;
  }
  if (isError || !report) {
    return (
      <EmptyState
        icon={FileWarning}
        title={(error as { status?: number })?.status === 404 ? "Session not found" : "Could not load report"}
        hint={error?.message}
        action={<Button asChild variant="secondary"><Link to="/sessions">Back to history</Link></Button>}
      />
    );
  }

  const { exercise, summary, rules, history, stats, session } = report as SessionReport;
  // Session extremes — feed the Mistakes card's best/worst footnote cells.
  const extremes = pickBestWorst(history);
  const rating = scoreRating(summary.score);

  const toggleRep = (n: number) =>
    setOpenReps((cur) => {
      const next = new Set(cur);
      if (next.has(n)) next.delete(n); else next.add(n);
      return next;
    });

  const onDownload = () => {
    if (!sessionId) return;
    setDownloading(true);
    downloadSessionReport(sessionId, exercise.name)
      .then(() => push("Report downloaded"))
      .catch((e: Error) => push(e.message, "error"))
      .finally(() => setDownloading(false));
  };

  return (
    <div className="space-y-6">
      <header className="flex items-start gap-3">
        <Button variant="ghost" size="icon" asChild aria-label="Back">
          <Link to="/sessions"><ArrowLeft /></Link>
        </Button>
        <div className="min-w-0 flex-1">
          <h1 className="text-2xl font-bold tracking-tight">{exercise.name}</h1>
          <p className="text-sm text-muted-foreground">
            {formatDate(session?.recorded_at ?? null)} · {exercise.muscle_groups.join(", ")} · {exercise.camera === "side" ? "side view" : "front view"}
          </p>
        </div>
        <Tooltip>
          <TooltipTrigger asChild>
            <Button variant="outline" size="icon" onClick={onDownload} disabled={downloading} aria-label="Download report JSON">
              <FileJson />
            </Button>
          </TooltipTrigger>
          <TooltipContent>Download the raw report (JSON)</TooltipContent>
        </Tooltip>
      </header>

      {/* Hero: score + headline numbers */}
      <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
        className="grid gap-4 rounded-2xl border border-border/60 bg-card p-5 md:grid-cols-[auto_1fr]">
        <div className="flex flex-col items-center justify-center gap-2 md:px-4">
          <ScoreRing score={summary.score} label="Session" />
          <Badge
            variant={rating.tone === "success" ? "success" : rating.tone === "warning" ? "warning" : rating.tone === "destructive" ? "destructive" : "outline"}
            className="px-3"
          >
            {rating.label}
          </Badge>
        </div>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
          <StatCard label="Total reps" value={summary.total_reps} icon={Gauge} />
          <StatCard label="Good" value={summary.good_reps} valueClassName="text-success" icon={CheckCircle2} />
          <StatCard label="Bad" value={summary.bad_reps} valueClassName={summary.bad_reps ? "text-destructive" : undefined} icon={XCircle} />
          <StatCard
            label="Accuracy"
            value={`${summary.accuracy.toFixed(0)}%`}
            hint={`${summary.good_reps}/${summary.total_reps} reps passed every check`}
            icon={Target}
          />
          <StatCard
            label="Avg rep"
            value={formatSeconds(summary.average_rep_duration)}
            hint={`${formatSeconds(summary.fastest_rep)} – ${formatSeconds(summary.slowest_rep)} range`}
            icon={Timer}
          />
          <StatCard label="Workout time" value={formatSeconds(summary.total_workout_duration)} icon={Timer} />
        </div>
      </motion.div>

      <div className="grid gap-4 lg:grid-cols-3">
        {/* Score per repetition — line plot (successor of the bar chart) */}
        <ScoreProgression history={history} />

        {/* Mistakes */}
        <Card>
          <CardHeader>
            <CardTitle>Mistakes</CardTitle>
            <CardDescription>
              {summary.most_common_error
                ? `Most common: ${titleCase(summary.most_common_error)}`
                : "No mistakes in this session"}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {Object.entries(summary.common_errors).length === 0 && (
              <p className="py-6 text-center text-sm text-muted-foreground">Perfect form — nothing failed.</p>
            )}
            {Object.entries(summary.common_errors).map(([rule, count], i) => {
              const def = rules.find((r) => r.name === rule);
              const stat = stats?.rules.find((s) => s.rule === rule);
              return (
                <div key={rule} className="space-y-1.5">
                  <div className="flex items-center justify-between text-sm">
                    <span className="font-medium">{titleCase(rule)}</span>
                    <Badge variant={i === 0 ? "destructive" : "warning"}>{count}×</Badge>
                  </div>
                  <Progress
                    value={(count / Math.max(...Object.values(summary.common_errors))) * 100}
                    indicatorClassName="bg-destructive/70"
                  />
                  {/* compact coaching: measured-vs-target + one-line fix */}
                  {def && avgTargetText(def, stat?.avg_measured_value) && (
                    <p className="text-[11px] tabular-nums text-muted-foreground">
                      {avgTargetText(def, stat?.avg_measured_value)}
                    </p>
                  )}
                  {def && (
                    <p className="flex items-start gap-1.5 text-xs text-foreground/80">
                      <Lightbulb className="mt-0.5 size-3.5 shrink-0 text-warning" />
                      {tipShortFor(def)}
                    </p>
                  )}
                </div>
              );
            })}
            {(stats || extremes) && (
              <div className="mt-4 grid grid-cols-3 gap-2 border-t border-border/60 pt-4 text-center">
                {extremes ? <ExtremesCell rep={extremes.best} kind="best" /> : <div />}
                {extremes ? <ExtremesCell rep={extremes.worst} kind="worst" /> : <div />}
                <div>
                  <p className="text-lg font-bold tabular-nums">{stats?.scores.std_dev?.toFixed(1) ?? "—"}</p>
                  <p className="text-[11px] text-muted-foreground">Consistency σ</p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Rule statistics */}
      {stats ? (
        <Card>
          <CardHeader>
            <CardTitle>Rule statistics</CardTitle>
            <CardDescription>Success rate over every evaluation in the session</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {stats.rules.map((row: RuleStats) => {
              const def = rules.find((r) => r.name === row.rule);
              return (
                <div key={row.rule} className="grid grid-cols-[1fr_auto] items-center gap-3 sm:grid-cols-[200px_1fr_auto]">
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium">{titleCase(row.rule)}</p>
                    {def && <p className="line-clamp-2 text-xs text-muted-foreground">{def.message}</p>}
                  </div>
                  <Progress
                    value={row.success_rate ?? 0}
                    className="hidden sm:block"
                    indicatorClassName={cn({
                      "bg-success": (row.success_rate ?? 0) >= 80,
                      "bg-warning": (row.success_rate ?? 0) >= 50 && (row.success_rate ?? 0) < 80,
                      "bg-destructive": (row.success_rate ?? 0) < 50,
                    })}
                  />
                  <div className="text-right">
                    <span className={cn("text-sm font-bold tabular-nums", scoreColor(row.success_rate))}>
                      {row.success_rate == null ? "N/A" : `${row.success_rate.toFixed(0)}%`}
                    </span>
                    <p className="text-[11px] text-muted-foreground tabular-nums">
                      {row.passed}/{row.evaluations} passed
                    </p>
                  </div>
                </div>
              );
            })}
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardContent className="py-8 text-center text-sm text-muted-foreground">
            Aggregated rule statistics are unavailable for this older export. Rep-level details below are intact.
          </CardContent>
        </Card>
      )}

      {/* Repetition history — expandable; the slim timeline strip maps each rep onto session time */}
      <Card>
        <CardHeader>
          <CardTitle>Repetition history</CardTitle>
          <CardDescription>Click a rep (row or timeline segment) for the full evaluation breakdown</CardDescription>
        </CardHeader>
        <CardContent className="space-y-2">
          <RepTimeline
            className="mb-3"
            history={history}
            fps={session?.fps ?? null}
            totalDuration={summary.total_workout_duration}
            openReps={openReps}
            onToggle={toggleRep}
          />
          {history.map((rep) => {
            const failed = rep.evaluations.filter((e) => !e.passed);
            const open = openReps.has(rep.number);
            return (
              <Fragment key={rep.number}>
                <button
                  onClick={() => toggleRep(rep.number)}
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
                    <div className="rounded-xl border border-border/60 bg-card/60 p-4">
                      <div className="flex flex-wrap gap-4 text-xs text-muted-foreground">
                        <span>Frames <strong className="text-foreground">{rep.start_frame ?? "—"} → {rep.end_frame ?? "—"}</strong></span>
                        <span>Duration <strong className="text-foreground">{formatSeconds(rep.duration_seconds)}</strong></span>
                        <span>Checks <strong className="text-foreground">{rep.evaluations.length}</strong></span>
                        <span>Failed <strong className={failed.length ? "text-destructive" : "text-foreground"}>{failed.length}</strong></span>
                      </div>
                      <RuleEvaluations rep={rep} rules={rules} />
                    </div>
                  </motion.div>
                )}
              </Fragment>
            );
          })}
        </CardContent>
      </Card>
    </div>
  );
}
