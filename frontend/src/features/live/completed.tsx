import { useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { ChevronRight, Download, FileJson, Loader2, RotateCcw, Trophy } from "lucide-react";
import type { LiveEnd, LiveState } from "@/schemas";
import { downloadSessionReport, useSession } from "@/lib/api/sessions";
import { useToast } from "@/providers/toast";
import { formatClock, formatSeconds, scoreColor } from "@/lib/format";
import { Button } from "@/components/ui/button";
import { ScoreRing, StatCard } from "@/components/shared";

/**
 * Post-workout column — everything the page shows once the engine finishes:
 *
 * - `WorkoutSummary` — the large view that replaces the video stage. It
 *   carries every end-of-workout number exactly once (score, reps, good/bad,
 *   accuracy, duration, processing time), so the live sidebar cards that
 *   reported those values during the workout step aside.
 * - `WorkoutActions` — the action block rendered directly under the summary
 *   box: View full report, Download JSON, Download video, Start new workout.
 *
 * Numbers prefer the exported report (the source of truth, fetched through
 * the existing sessions query) and fall back to the end payload, then the
 * last live-stream frame when no report was exported.
 */

/** Large workout-summary view — fills the stage area after completion. */
export function WorkoutSummary({
  result,
  lastState,
  processingSeconds,
  exerciseName,
}: {
  result: LiveEnd | null;
  lastState: LiveState | null;
  processingSeconds: number | null;
  exerciseName: string;
}) {
  const sessionId = result?.session_id;
  const { data: report, isLoading } = useSession(sessionId);

  const summary = report?.summary;
  const totalReps = summary?.total_reps ?? result?.reps ?? lastState?.reps ?? 0;
  const good = summary?.good_reps ?? lastState?.good ?? 0;
  const bad = summary?.bad_reps ?? lastState?.bad ?? 0;
  const accuracy = summary?.accuracy ?? (totalReps > 0 ? (good / totalReps) * 100 : null);
  const score = summary?.score ?? lastState?.live_score ?? null;
  const duration = summary?.total_workout_duration ?? lastState?.elapsed ?? null;

  const caveats = !result || result?.export_error || result?.rendered_error;

  return (
    <motion.section
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full rounded-2xl border border-success/40 bg-card p-5 sm:p-6"
    >
      <header className="flex items-center gap-3">
        <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-success/15">
          <Trophy className="size-5 text-success" />
        </span>
        <div className="min-w-0 flex-1">
          <p className="text-base font-semibold">Workout completed</p>
          <p className="truncate text-sm text-muted-foreground">{exerciseName}</p>
        </div>
        {sessionId && isLoading && (
          <span className="flex items-center gap-1.5 text-[11px] text-muted-foreground">
            <Loader2 className="size-3 animate-spin" /> syncing report…
          </span>
        )}
      </header>

      {/* Every end-of-workout number lives here — the sidebar sheds its copies */}
      <div className="mt-6 flex flex-col items-center gap-6 sm:flex-row sm:gap-8">
        <ScoreRing score={score} size={128} label="Score" />
        <div className="grid w-full min-w-0 flex-1 grid-cols-2 gap-3 sm:grid-cols-3">
          <StatCard label="Reps" value={totalReps} />
          <StatCard label="Good" value={good} valueClassName="text-success" />
          <StatCard label="Bad" value={bad} valueClassName={bad > 0 ? "text-destructive" : undefined} />
          <StatCard
            label="Accuracy"
            value={accuracy != null ? `${accuracy.toFixed(0)}%` : "—"}
            valueClassName={scoreColor(accuracy)}
          />
          <StatCard label="Duration" value={duration != null ? formatClock(duration) : "—"} />
          <StatCard label="Processing" value={processingSeconds != null ? formatSeconds(processingSeconds) : "—"} />
        </div>
      </div>

      {/* Caveats, if any part of the export pipeline failed */}
      {caveats && (
        <div className="mt-5 space-y-1.5 border-t border-border/60 pt-4">
          {!result && (
            <p className="text-xs text-muted-foreground">
              The stream closed before the engine sent its summary — showing the last known numbers.
            </p>
          )}
          {result?.export_error && <p className="text-xs text-warning">Report export failed: {result.export_error}</p>}
          {result?.rendered_error && (
            <p className="text-xs text-warning">Rendered video failed: {result.rendered_error}</p>
          )}
        </div>
      )}
    </motion.section>
  );
}

/** Post-workout actions — rendered directly under the workout-summary box. */
export function WorkoutActions({
  result,
  exerciseName,
  onNewWorkout,
}: {
  result: LiveEnd | null;
  exerciseName: string;
  onNewWorkout: () => void;
}) {
  const { push } = useToast();
  const sessionId = result?.session_id;
  const [downloading, setDownloading] = useState(false);

  const onDownload = () => {
    if (!sessionId) return;
    setDownloading(true);
    downloadSessionReport(sessionId, exerciseName)
      .then(() => push("Report downloaded"))
      .catch((e: Error) => push(e.message, "error"))
      .finally(() => setDownloading(false));
  };

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="space-y-2">
      {sessionId ? (
        <Button className="w-full" asChild>
          <Link to={`/sessions/${sessionId}`}>
            View full report <ChevronRight />
          </Link>
        </Button>
      ) : (
        <p className="rounded-lg bg-muted/50 px-3 py-2 text-center text-xs text-muted-foreground">
          No report was exported for this run — enable “Export session reports” in Settings to save one.
        </p>
      )}
      {(sessionId || result?.rendered_video) && (
        <div className="flex gap-2">
          {sessionId && (
            <Button variant="secondary" className="flex-1" disabled={downloading} onClick={onDownload}>
              {downloading ? <Loader2 className="animate-spin" /> : <FileJson />}
              {downloading ? "Preparing…" : "Download JSON"}
            </Button>
          )}
          {result?.rendered_video && (
            <Button variant="secondary" className="flex-1" asChild>
              <a href={`/api/downloads/rendered/${result.rendered_video}`} download>
                <Download /> Download video
              </a>
            </Button>
          )}
        </div>
      )}
      <Button variant="outline" className="w-full" onClick={onNewWorkout}>
        <RotateCcw /> Start new workout
      </Button>
    </motion.div>
  );
}
