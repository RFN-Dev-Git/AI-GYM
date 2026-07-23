import { useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import {
  ArrowLeft, CheckCircle2, CircleX, FileVideo, Loader2, Play, ScanFace, Square, Trash2, Upload, Video, X, XCircle,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { formatBytes, formatClock, titleCase } from "@/lib/format";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { useToast } from "@/providers/toast";
import { ScoreRing } from "@/components/shared";
import { useDeleteUpload, uploadVideo, useUploads } from "@/lib/api/uploads";
import type { LiveSource } from "@/lib/api/live";
import { useLiveSession } from "./use-live-session";
import { derivePhase } from "./lifecycle";
import { LifecycleBar, StatusPill } from "./status";
import { LiveFeedbackPanel } from "./feedback";
import { WorkoutActions, WorkoutSummary } from "./completed";

/**
 * Live workout page — a lifecycle-driven coaching room:
 * Set up → Ready → Workout → Completed.
 *
 * Layout is reserved up front (video stage, stats, feedback panel, controls)
 * so nothing shifts while streaming; navigation to the session report only
 * happens through the completion actions' explicit button.
 *
 * Once the workout ends, the finished video AND the whole coaching HUD
 * (rep tiles, stage card, feedback panel, form checks) step aside: only the
 * centered Workout-completed box remains, with its actions directly
 * underneath. Every end-of-workout element appears exactly once.
 */
export function LivePage() {
  const { exerciseId } = useParams();
  const { push } = useToast();
  const [source, setSource] = useState<LiveSource>("webcam");
  // Web-app video flow: pick a local file → upload → stream `upload:<id>`.
  const [file, setFile] = useState<File | null>(null);
  const [previousId, setPreviousId] = useState<string | null>(null);
  const [uploadPct, setUploadPct] = useState<number | null>(null);
  const [confirmRemove, setConfirmRemove] = useState(false);
  // Probed dimensions of a locally picked file — lets the stage reserve the
  // video's true aspect ratio before the first frame streams in.
  const [probeSize, setProbeSize] = useState<{ w: number; h: number } | null>(null);
  const fileInput = useRef<HTMLInputElement | null>(null);
  // Exact start arguments — lets the error overlay retry the identical session.
  const lastArgs = useRef<{ source: LiveSource; video?: string } | null>(null);
  const { data: uploads } = useUploads();
  const removeUpload = useDeleteUpload();
  const {
    status, state, result, error, frameSize, processingSeconds, bindCanvas, start, stop, reset,
  } = useLiveSession(exerciseId);

  const canStart = source === "webcam" || file !== null || previousId !== null;
  const phase = derivePhase(status, canStart);
  // During setup the stage keeps a neutral 16/9 reservation — picking a
  // (portrait) file must not shift the layout; the real aspect applies from
  // the connecting phase onward (probed first, decoded frames after).
  const frameAspect = status === "idle" ? null : (frameSize ?? probeSize);
  const exerciseName = state?.exercise ?? titleCase(exerciseId ?? "");

  // Probe a picked file's intrinsic size (metadata only, instantly revoked).
  useEffect(() => {
    if (!file) {
      setProbeSize(null);
      return;
    }
    const url = URL.createObjectURL(file);
    const el = document.createElement("video");
    el.preload = "metadata";
    el.onloadedmetadata = () => {
      setProbeSize(el.videoWidth && el.videoHeight ? { w: el.videoWidth, h: el.videoHeight } : null);
      URL.revokeObjectURL(url);
    };
    el.onerror = () => URL.revokeObjectURL(url);
    el.src = url;
    // Cancel a stale probe if the file is cleared/replaced before it loads.
    return () => {
      el.onloadedmetadata = null;
      el.onerror = null;
      el.src = "";
    };
  }, [file]);

  // One toast marks the transition into the completed phase (no navigation).
  useEffect(() => {
    if (status === "ended") push("Workout complete");
  }, [status, push]);

  const clearFile = () => {
    setFile(null);
    setProbeSize(null);
    if (fileInput.current) fileInput.current.value = "";
  };

  // Upload (if needed) then open the live stream. Upload failures surface as
  // toasts and the page stays on the setup step.
  const begin = async () => {
    if (source === "webcam") {
      lastArgs.current = { source: "webcam" };
      return start("webcam");
    }
    try {
      if (file) {
        setUploadPct(0);
        const uploaded = await uploadVideo(file, setUploadPct);
        lastArgs.current = { source: "video", video: `upload:${uploaded.id}` };
        start("video", `upload:${uploaded.id}`);
      } else if (previousId) {
        lastArgs.current = { source: "video", video: `upload:${previousId}` };
        start("video", `upload:${previousId}`);
      }
    } catch (e) {
      push((e as Error).message, "error");
    } finally {
      setUploadPct(null);
    }
  };

  const retry = () => {
    if (lastArgs.current) start(lastArgs.current.source, lastArgs.current.video);
    else reset();
  };

  // "Start new workout": same exercise, back to a pristine setup step.
  const newWorkout = () => {
    reset();
    clearFile();
    setPreviousId(null);
    setConfirmRemove(false);
    lastArgs.current = null;
  };

  const confirmRemoveUpload = () => {
    if (!previousId) return;
    removeUpload.mutate(previousId, {
      onSuccess: () => {
        push("Upload removed");
        setPreviousId(null);
        setConfirmRemove(false);
      },
      onError: (e) => {
        push(e.message, "error");
        setConfirmRemove(false);
      },
    });
  };

  return (
    <div className="space-y-4">
      {/* Top bar */}
      <header className="flex flex-wrap items-center gap-3">
        <Button variant="ghost" size="icon" asChild aria-label="Back">
          <Link to="/exercises"><ArrowLeft /></Link>
        </Button>
        <div className="min-w-0 flex-1">
          <h1 className="truncate text-xl font-bold tracking-tight">{exerciseName}</h1>
        </div>
        <StatusPill status={status} ready={canStart} />
        {state?.is_3d && (
          <Badge variant="primary" className="gap-1">
            <span className="size-1.5 rounded-full bg-white animate-pulse" /> 3D Mode
          </Badge>
        )}
        {state?.side && (
          <Badge variant="outline">
            <ScanFace className="size-3" /> {state.side === "both" ? "Front view" : `${titleCase(state.side)} side`}
          </Badge>
        )}
        {status === "live" && state && <Badge variant="outline">{state.fps.toFixed(0)} fps</Badge>}
      </header>

      {/* Workout lifecycle */}
      <LifecycleBar phase={phase} />

      {status === "ended" ? (
        /* Post-workout: the finished video AND the coaching HUD step aside —
           only the centered Workout-completed box with its actions remains */
        <div className="mx-auto flex w-full max-w-3xl flex-col gap-4">
          <WorkoutSummary
            result={result}
            lastState={state}
            processingSeconds={processingSeconds}
            exerciseName={exerciseName}
          />
          <WorkoutActions result={result} exerciseName={exerciseName} onNewWorkout={newWorkout} />
        </div>
      ) : (
      <div className="grid gap-4 lg:grid-cols-3">
        {/* Video stage — aspect ratio follows the actual video, never stretched */}
        <section
          className="relative w-full self-start overflow-hidden rounded-2xl border border-border/60 bg-black lg:col-span-2"
          style={{
            aspectRatio: frameAspect ? `${frameAspect.w} / ${frameAspect.h}` : "16 / 9",
            maxHeight: "min(72vh, 56rem)",
          }}
        >
          <canvas ref={bindCanvas} className="absolute inset-0 block h-full w-full object-contain" />
          <AnimatePresence mode="wait" initial={false}>
            {(status === "idle" || status === "connecting") && (
              <motion.div
                key={status}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.2 }}
              className="absolute inset-0 flex flex-col bg-background/80 p-5 backdrop-blur-sm"
            >
              {status === "connecting" ? (
                <div className="flex flex-1 flex-col items-center justify-center gap-3 text-center">
                  <Loader2 className="size-10 animate-spin text-primary" />
                  <p className="text-sm font-medium">Connecting to the engine…</p>
                  <p className="max-w-xs text-xs text-muted-foreground">
                    Warming up the video pipeline — the first frames are on their way.
                  </p>
                </div>
              ) : (
                <>
                  {/* Source & input cluster — flexible: it may grow, shrink and
                      animate freely; it can never move the pinned Start button */}
                  <div className="slim-scroll flex min-h-0 flex-1 flex-col items-center justify-center gap-3 overflow-y-auto">
                    <span className="grid size-14 flex-none place-items-center rounded-2xl bg-primary/10">
                      <Video className="size-7 text-primary" />
                    </span>
                    <p className="text-sm font-semibold">Set up your workout</p>
                    <div className="flex gap-2">
                      {(["webcam", "video"] as const).map((s) => (
                        <button
                          key={s}
                          onClick={() => setSource(s)}
                          className={cn(
                            "rounded-full border px-4 py-2 text-sm font-medium capitalize transition-colors",
                            source === s
                              ? "border-primary/60 bg-primary/15 text-primary"
                              : "border-border bg-card text-muted-foreground",
                          )}
                        >
                          {s}
                        </button>
                      ))}
                    </div>

                    {source === "video" && (
                      <motion.div
                        initial={{ opacity: 0, y: 6 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="flex w-full max-w-sm flex-col items-stretch gap-2 rounded-xl border border-border/60 bg-card p-3"
                      >
                        <input
                          ref={fileInput}
                          type="file"
                          accept="video/*,.mp4,.mov,.mkv,.avi,.webm,.m4v"
                          className="hidden"
                          onChange={(e) => {
                            setFile(e.target.files?.[0] ?? null);
                            setPreviousId(null);
                            setConfirmRemove(false);
                          }}
                        />
                        <Button variant="secondary" onClick={() => fileInput.current?.click()}>
                          <Upload /> {file ? "Choose another video" : "Choose a video from your computer"}
                        </Button>
                        {file && (
                          <p className="flex items-center justify-center gap-2 text-center text-xs text-muted-foreground">
                            <FileVideo className="size-3.5 shrink-0 text-primary" />
                            <span className="truncate">{file.name}</span>
                            <span className="shrink-0">{formatBytes(file.size)}</span>
                            <button
                              onClick={clearFile}
                              aria-label="Clear selected video"
                              className="shrink-0 rounded-full p-0.5 transition-colors hover:text-destructive"
                            >
                              <X className="size-3.5" />
                            </button>
                          </p>
                        )}
                        {uploads && uploads.length > 0 && (
                          <label className="mt-1 block text-xs text-muted-foreground">
                            Or use a previous upload
                            <select
                              className="mt-1 h-9 w-full rounded-lg border border-input bg-card px-2 text-sm text-foreground"
                              value={previousId ?? ""}
                              onChange={(e) => {
                                setPreviousId(e.target.value || null);
                                setConfirmRemove(false);
                                clearFile();
                              }}
                            >
                              <option value="">—</option>
                              {uploads.map((u) => (
                                <option key={u.id} value={u.id}>
                                  {u.name} · {formatBytes(u.size)}
                                </option>
                              ))}
                            </select>
                          </label>
                        )}
                        {previousId && (
                          <div className="flex items-center justify-between gap-2 rounded-lg border border-border/50 bg-background/40 px-2.5 py-1.5">
                            <span className="truncate text-[11px] text-muted-foreground">Stored on the host</span>
                            {confirmRemove ? (
                              <span className="flex items-center gap-1">
                                <Button
                                  variant="destructive"
                                  size="sm"
                                  className="h-7 px-2"
                                  disabled={removeUpload.isPending}
                                  onClick={confirmRemoveUpload}
                                >
                                  {removeUpload.isPending ? <Loader2 className="animate-spin" /> : null}
                                  Confirm
                                </Button>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  className="h-7 px-2"
                                  onClick={() => setConfirmRemove(false)}
                                >
                                  Keep
                                </Button>
                              </span>
                            ) : (
                              <button
                                className="flex shrink-0 items-center gap-1 text-[11px] font-medium text-muted-foreground transition-colors hover:text-destructive"
                                onClick={() => setConfirmRemove(true)}
                              >
                                <Trash2 className="size-3" /> Remove
                              </button>
                            )}
                          </div>
                        )}
                      </motion.div>
                    )}

                    <p className="max-w-xs text-center text-xs text-muted-foreground">
                      {source === "webcam"
                        ? "Video is captured on the host machine and streamed here in real time."
                        : "Your video is uploaded to the host, processed by the engine, and streamed back live — the report follows on this page."}
                    </p>
                  </div>

                  {/* Action cluster — fixed geometry: the progress slot, the
                      Start button and the hint line keep constant heights, so
                      Start never resizes, jumps or shifts while setting up */}
                  <div className="flex flex-none flex-col items-center gap-2">
                    <div className="flex h-9 items-center justify-center">
                      {uploadPct !== null && (
                        <div className="w-56 space-y-1">
                          <Progress value={uploadPct} />
                          <p className="text-center text-[11px] text-muted-foreground">Uploading video… {uploadPct}%</p>
                        </div>
                      )}
                    </div>
                    <Button size="lg" disabled={!canStart || uploadPct !== null} onClick={begin}>
                      <Play /> Start workout
                    </Button>
                    <p className={cn("h-4 text-center text-[11px] font-medium", !canStart && uploadPct === null && "text-warning")}>
                      {source === "video" && !canStart && uploadPct === null
                        ? "Pick a video file or choose a previous upload to enable Start."
                        : ""}
                    </p>
                  </div>
                </>
              )}
            </motion.div>
            )}
          </AnimatePresence>

          {state?.adapting && status === "live" && (
            <div className="absolute left-3 top-3 rounded-lg bg-black/60 px-3 py-1.5 text-xs font-medium text-white backdrop-blur">
              Detecting camera side…
            </div>
          )}
          {status === "error" && (
            <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 bg-background/80 p-6 text-center backdrop-blur-sm">
              <CircleX className="size-10 text-destructive" />
              <p className="max-w-md text-sm font-medium">{error}</p>
              <div className="flex gap-2">
                <Button variant="secondary" onClick={retry}>Retry session</Button>
                <Button variant="ghost" onClick={reset}>Back to setup</Button>
              </div>
            </div>
          )}
        </section>

        {/* Coaching HUD — setup & workout only (the grid itself is replaced
            by the centered summary column once the workout completes) */}
        <aside className="flex flex-col gap-4">
          {/* Live telemetry */}
          <div className="grid grid-cols-3 gap-3">
            <div className="rounded-xl border border-border/60 bg-card p-3 text-center">
              <p className="text-3xl font-bold tabular-nums">{state?.reps ?? 0}</p>
              <p className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground">Reps</p>
            </div>
            <div className="rounded-xl border border-success/30 bg-success/5 p-3 text-center">
              <p className="text-3xl font-bold tabular-nums text-success">{state?.good ?? 0}</p>
              <p className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground">Good</p>
            </div>
            <div className="rounded-xl border border-destructive/30 bg-destructive/5 p-3 text-center">
              <p className="text-3xl font-bold tabular-nums text-destructive">{state?.bad ?? 0}</p>
              <p className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground">Bad</p>
            </div>
          </div>

          <div className="flex items-center justify-between gap-3 rounded-xl border border-border/60 bg-card p-4">
            <div className="space-y-2">
              <p className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground">Stage</p>
              <Badge variant="primary" className="text-sm">{state?.stage ?? "—"}</Badge>
              <p className="text-xs text-muted-foreground">
                Elapsed <span className="font-mono">{formatClock(state?.elapsed ?? 0)}</span>
              </p>
            </div>
            <div className="space-y-2 text-right">
              <p className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground">Joint angle</p>
              <p className="text-2xl font-bold tabular-nums">{state?.angle != null ? `${state.angle.toFixed(0)}°` : "—"}</p>
            </div>
            <ScoreRing score={state?.live_score ?? null} size={92} label="Form" />
          </div>

          {/* Feedback strip — Standing by → Good form → warnings */}
          <LiveFeedbackPanel status={status} feedback={state?.feedback ?? []} />

          {/* Rule lights (available once the stream reports them) */}
          {state && state.rules.length > 0 && (
            <div className="rounded-xl border border-border/60 bg-card p-4">
              <p className="mb-2 flex items-center justify-between text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
                <span>Form checks</span>
                {state.is_3d && <span className="text-[9px] bg-primary/10 text-primary px-1.5 py-0.5 rounded">3D • {state.rules.filter(r=>r.is_3d).length}/{state.rules.length} 3D</span>}
              </p>
              <ul className="space-y-2">
                {state.rules.map((r) => (
                  <li key={r.name} className="flex items-center justify-between gap-2 text-sm">
                    <span className="flex min-w-0 items-center gap-2">
                      {r.passed
                        ? <CheckCircle2 className="size-4 shrink-0 text-success" />
                        : <XCircle className={cn("size-4 shrink-0", r.severity === "warning" ? "text-warning" : "text-destructive")} />}
                      <span className="truncate">{titleCase(r.name)}</span>
                      {r.severity === "warning" && !r.passed && <Badge variant="warning" className="text-[9px] px-1 py-0">WARN</Badge>}
                      {r.severity === "error" && !r.passed && <Badge variant="destructive" className="text-[9px] px-1 py-0">ERR</Badge>}
                    </span>
                    <span className="flex items-center gap-1.5">
                      {r.is_3d && <span className="text-[9px] text-primary">3D</span>}
                      <span className="shrink-0 font-mono text-xs text-muted-foreground">
                        {r.value != null ? r.value.toFixed(0) : "—"}
                      </span>
                    </span>
                  </li>
                ))}
              </ul>
              <p className="mt-2 text-[10px] text-muted-foreground">⚠️ WARNING = GOOD with reduced score (80) • ❌ ERROR = BAD rep (score 50)</p>
            </div>
          )}

          {/* Controls — same reserved slot across phases */}
          <div className="mt-auto flex flex-col gap-3">
            {status === "live" && (
              <Button variant="destructive" size="lg" className="w-full" onClick={stop}>
                <Square /> End workout
              </Button>
            )}
            {status === "connecting" && (
              <div className="flex gap-2">
                <Button variant="secondary" size="lg" className="flex-1" disabled>
                  <Loader2 className="animate-spin" /> Connecting…
                </Button>
                <Button variant="outline" size="lg" onClick={reset} aria-label="Cancel">
                  <X />
                </Button>
              </div>
            )}
          </div>
        </aside>
      </div>
      )}
    </div>
  );
}
