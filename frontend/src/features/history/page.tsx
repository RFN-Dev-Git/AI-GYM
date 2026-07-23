import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowDownUp, ChevronRight, History, Search, Trash2, Video } from "lucide-react";
import { useDeleteSession, useSessions } from "@/lib/api/sessions";
import type { SessionListItem } from "@/schemas";
import { cn } from "@/lib/utils";
import { formatDate, formatSeconds, scoreColor } from "@/lib/format";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { EmptyState } from "@/components/shared";
import { useToast } from "@/providers/toast";

type SortKey = "date" | "score" | "reps";
const SORTS: { id: SortKey; label: string }[] = [
  { id: "date", label: "Newest" },
  { id: "score", label: "Score" },
  { id: "reps", label: "Reps" },
];

export function HistoryPage() {
  const { data: sessions, isLoading, isError, refetch } = useSessions();
  const remove = useDeleteSession();
  const { push } = useToast();
  const [query, setQuery] = useState("");
  const [sort, setSort] = useState<SortKey>("date");
  const [exerciseFilter, setExerciseFilter] = useState<string | null>(null);
  const [confirm, setConfirm] = useState<SessionListItem | null>(null);

  const exerciseNames = useMemo(
    () => [...new Set((sessions ?? []).map((s) => s.exercise))].sort(),
    [sessions],
  );

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    const list = (sessions ?? []).filter((s) => {
      if (exerciseFilter && s.exercise !== exerciseFilter) return false;
      if (!q) return true;
      return s.exercise.toLowerCase().includes(q) || (s.most_common_error ?? "").toLowerCase().includes(q);
    });
    return [...list].sort((a, b) =>
      sort === "score"
        ? (b.score ?? -1) - (a.score ?? -1)
        : sort === "reps"
          ? b.total_reps - a.total_reps
          : (b.recorded_at ?? "").localeCompare(a.recorded_at ?? ""),
    );
  }, [sessions, query, sort, exerciseFilter]);

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-40" />
        {Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-16" />)}
      </div>
    );
  }

  if (isError) {
    return (
      <EmptyState icon={Video} title="Backend unreachable"
        hint="Start the API, then retry."
        action={<Button onClick={() => refetch()}>Retry</Button>}
      />
    );
  }

  return (
    <div className="space-y-6">
      <header className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Workout history</h1>
          <p className="text-sm text-muted-foreground">{filtered.length} session{filtered.length === 1 ? "" : "s"}</p>
        </div>
        <div className="relative w-full sm:w-72">
          <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search…" className="pl-9" />
        </div>
      </header>

      <div className="flex flex-wrap items-center gap-2">
        <ArrowDownUp className="size-4 text-muted-foreground" />
        <div className="flex rounded-lg border border-border bg-card p-0.5">
          {SORTS.map((s) => (
            <button
              key={s.id}
              onClick={() => setSort(s.id)}
              className={cn(
                "rounded-md px-3 py-1 text-xs font-medium transition-colors",
                sort === s.id ? "bg-primary/15 text-primary" : "text-muted-foreground hover:text-foreground",
              )}
            >
              {s.label}
            </button>
          ))}
        </div>
        <span className="mx-1 hidden h-5 w-px bg-border sm:block" />
        <Badge variant={exerciseFilter === null ? "primary" : "outline"} className="cursor-pointer" onClick={() => setExerciseFilter(null)}>
          All exercises
        </Badge>
        {exerciseNames.map((name) => (
          <Badge
            key={name}
            variant={exerciseFilter === name ? "primary" : "outline"}
            className="cursor-pointer"
            onClick={() => setExerciseFilter((cur) => (cur === name ? null : name))}
          >
            {name}
          </Badge>
        ))}
      </div>

      {filtered.length === 0 ? (
        <EmptyState
          icon={History}
          title="No sessions found"
          hint={query || exerciseFilter ? "Try clearing the search or filters." : "Complete a live workout and it will appear here."}
          action={!query && !exerciseFilter ? <Button asChild><Link to="/exercises">Start training</Link></Button> : undefined}
        />
      ) : (
        <div className="space-y-2">
          {filtered.map((s, i) => (
            <motion.div key={s.id} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: Math.min(i, 10) * 0.03 }}
              className="group flex items-center gap-3 rounded-xl border border-border/60 bg-card px-4 py-3 transition-colors hover:border-primary/40"
            >
              <Link to={`/sessions/${s.id}`} className="flex min-w-0 flex-1 items-center gap-4">
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-semibold">{s.exercise}</p>
                  <p className="text-xs text-muted-foreground">{formatDate(s.recorded_at)}</p>
                </div>
                <div className="hidden text-center sm:block">
                  <p className="text-sm font-medium tabular-nums">{s.total_reps}</p>
                  <p className="text-[11px] text-muted-foreground">reps</p>
                </div>
                <div className="hidden text-center sm:block">
                  <p className="text-sm font-medium tabular-nums">{s.accuracy.toFixed(0)}%</p>
                  <p className="text-[11px] text-muted-foreground">accuracy</p>
                </div>
                <div className="hidden text-center sm:block">
                  <p className="text-sm font-medium tabular-nums">{formatSeconds(s.duration)}</p>
                  <p className="text-[11px] text-muted-foreground">duration</p>
                </div>
                <span className={cn("w-10 text-right text-lg font-bold tabular-nums", scoreColor(s.score))}>
                  {s.score?.toFixed(0) ?? "—"}
                </span>
                <ChevronRight className="size-4 text-muted-foreground transition-transform group-hover:translate-x-0.5" />
              </Link>
              <Button
                variant="ghost"
                size="icon"
                aria-label={`Delete ${s.exercise} session`}
                className="text-muted-foreground hover:text-destructive"
                onClick={() => setConfirm(s)}
              >
                <Trash2 className="size-4" />
              </Button>
            </motion.div>
          ))}
        </div>
      )}

      {/* Delete confirmation */}
      <Dialog open={confirm !== null} onOpenChange={(open) => !open && setConfirm(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete this session?</DialogTitle>
            <DialogDescription>
              {confirm && `${confirm.exercise} · ${formatDate(confirm.recorded_at)}`} — this removes the exported
              report file permanently. This cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setConfirm(null)}>Cancel</Button>
            <Button
              variant="destructive"
              disabled={remove.isPending}
              onClick={() =>
                confirm &&
                remove.mutate(confirm.id, {
                  onSuccess: () => {
                    push("Session deleted");
                    setConfirm(null);
                  },
                  onError: (e) => push(e.message, "error"),
                })
              }
            >
              <Trash2 /> Delete
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
