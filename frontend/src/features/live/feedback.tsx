import { AnimatePresence, motion } from "framer-motion";
import { AlertTriangle, Hourglass, ShieldCheck } from "lucide-react";
import { cn } from "@/lib/utils";
import type { LiveStatus } from "./use-live-session";

/**
 * Permanent "Live Feedback" panel — the coach's sports-dashboard strip.
 *
 * The panel itself never mounts/unmounts *during* a workout: its content
 * cross-fades between three states inside reserved space, so warnings
 * appearing or clearing never shift the surrounding layout. Once the workout
 * completes the panel steps aside entirely — the page's post-workout column
 * (workout summary + actions) carries everything from there.
 */
export function LiveFeedbackPanel({ status, feedback }: { status: LiveStatus; feedback: string[] }) {
  const working = status === "connecting" || status === "live";
  const issues = feedback.length > 0;
  const mode = issues ? "issues" : working ? "clean" : "waiting";

  return (
    <section
      aria-live="polite"
      className={cn(
        "rounded-xl border bg-card p-4 transition-colors duration-300",
        issues ? "border-warning/50" : status === "live" ? "border-success/40" : "border-border/60",
      )}
    >
      <header className="mb-3 flex items-center justify-between gap-2">
        <p className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground">Live Feedback</p>
        {status === "live" && (
          <span className="flex items-center gap-1.5 text-[11px] font-medium text-muted-foreground">
            <span className={cn("size-1.5 animate-pulse rounded-full", issues ? "bg-warning" : "bg-success")} />
            {issues ? `${feedback.length} active` : "monitoring"}
          </span>
        )}
      </header>

      {/* min-h reserves the stage: state swaps cross-fade, never reflow the page */}
      <div className="min-h-[5.5rem]">
        <AnimatePresence mode="wait" initial={false}>
          {mode === "issues" && (
            <motion.ul
              key="issues"
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -4 }}
              transition={{ duration: 0.18 }}
              className="slim-scroll max-h-40 space-y-1.5 overflow-y-auto"
            >
              <AnimatePresence initial={false}>
                {feedback.map((msg) => (
                  <motion.li
                    layout
                    key={msg}
                    initial={{ opacity: 0, x: -8 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: 8 }}
                    transition={{ duration: 0.18 }}
                    className="flex items-start gap-2 rounded-lg bg-warning/10 px-2.5 py-1.5 text-sm font-medium text-warning"
                  >
                    <AlertTriangle className="mt-0.5 size-4 shrink-0" />
                    <span className="min-w-0">{msg}</span>
                  </motion.li>
                ))}
              </AnimatePresence>
            </motion.ul>
          )}
          {mode === "clean" && (
            <motion.div
              key="clean"
              initial={{ opacity: 0, scale: 0.96 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.96 }}
              transition={{ duration: 0.18 }}
              className="flex min-h-[5.5rem] flex-col items-center justify-center gap-1 text-center"
            >
              <ShieldCheck className="size-6 text-success" />
              <p className="text-sm font-semibold text-success">Good form</p>
              <p className="text-xs text-muted-foreground">No active issues</p>
            </motion.div>
          )}
          {mode === "waiting" && (
            <motion.div
              key="waiting"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.18 }}
              className="flex min-h-[5.5rem] flex-col items-center justify-center gap-1 text-center"
            >
              <Hourglass className="size-5 text-muted-foreground" />
              <p className="text-sm font-medium text-muted-foreground">Standing by</p>
              <p className="max-w-48 text-xs text-muted-foreground">
                Coach feedback appears here during the workout
              </p>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </section>
  );
}
