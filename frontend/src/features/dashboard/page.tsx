import { useMemo } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { LineChart, Line, ResponsiveContainer, Tooltip as ChartTooltip, XAxis, YAxis } from "recharts";
import {
  Activity, ArrowRight, Flame, Gauge, Play, Target, TrendingDown, TrendingUp, Trophy, Video,
} from "lucide-react";
import { useSessions } from "@/lib/api/sessions";
import { useExercises } from "@/lib/api/exercises";
import { formatDay, scoreColor, titleCase } from "@/lib/format";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState, StatCard } from "@/components/shared";
import { ExerciseCard } from "@/features/exercises/exercise-card";

function mean(values: number[]): number | null {
  return values.length ? values.reduce((a, b) => a + b, 0) / values.length : null;
}

export function DashboardPage() {
  const { data: sessions, isLoading, isError, refetch } = useSessions();
  const { data: exercises } = useExercises();

  // All dashboard aggregates derive from the same session list (single source).
  const stats = useMemo(() => {
    const list = sessions ?? [];
    const scores = list.map((s) => s.score).filter((v): v is number => v != null);
    const mistakes = new Map<string, number>();
    for (const s of list) {
      if (s.most_common_error) mistakes.set(s.most_common_error, (mistakes.get(s.most_common_error) ?? 0) + 1);
    }
    return {
      totalSessions: list.length,
      totalReps: list.reduce((a, s) => a + s.total_reps, 0),
      avgScore: mean(scores),
      bestScore: scores.length ? Math.max(...scores) : null,
      worstScore: scores.length ? Math.min(...scores) : null,
      avgAccuracy: mean(list.map((s) => s.accuracy)),
      mistakes: [...mistakes.entries()].sort((a, b) => b[1] - a[1]).slice(0, 5),
      trend: [...list]
        .filter((s) => s.recorded_at && s.score != null)
        .reverse()
        .map((s) => ({ day: formatDay(s.recorded_at), score: Math.round(s.score!) })),
      recent: list.slice(0, 5),
    };
  }, [sessions]);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-56" />
        <div className="grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-6">
          {Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-24" />)}
        </div>
        <Skeleton className="h-64" />
      </div>
    );
  }

  if (isError) {
    return (
      <EmptyState
        icon={Gauge}
        title="Backend unreachable"
        hint="Start the API (make backend from the repo root), then retry."
        action={<Button onClick={() => refetch()}>Retry</Button>}
      />
    );
  }

  const noSessions = stats.totalSessions === 0;

  return (
    <div className="space-y-8">
      <motion.header initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-2xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-sm text-muted-foreground">Your training at a glance.</p>
      </motion.header>

      {/* KPI grid */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
        <StatCard label="Avg Score" icon={Gauge} value={stats.avgScore?.toFixed(0) ?? "—"} valueClassName={scoreColor(stats.avgScore)} />
        <StatCard label="Best Score" icon={Trophy} value={stats.bestScore ?? "—"} valueClassName="text-success" />
        <StatCard label="Worst Score" icon={TrendingDown} value={stats.worstScore ?? "—"} valueClassName="text-warning" />
        <StatCard label="Accuracy" icon={Target} value={stats.avgAccuracy != null ? `${stats.avgAccuracy.toFixed(0)}%` : "—"} />
        <StatCard label="Total Reps" icon={Flame} value={stats.totalReps} />
        <StatCard label="Sessions" icon={Activity} value={stats.totalSessions} />
      </div>

      {noSessions ? (
        <EmptyState
          icon={Video}
          title="No workouts yet"
          hint="Start your first live session and the dashboard will fill up with your stats."
          action={<Button asChild><Link to="/exercises"><Play />Start training</Link></Button>}
        />
      ) : (
        <div className="grid gap-4 lg:grid-cols-3">
          {/* Progress over time */}
          <Card className="lg:col-span-2 animate-fade-up">
            <CardHeader>
              <CardTitle className="flex items-center gap-2"><TrendingUp className="size-4 text-primary" /> Progress over time</CardTitle>
              <CardDescription>Session score per workout</CardDescription>
            </CardHeader>
            <CardContent className="h-56">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={stats.trend} margin={{ top: 4, right: 8, bottom: 0, left: -18 }}>
                  <XAxis dataKey="day" tick={{ fontSize: 11 }} stroke="hsl(var(--muted-foreground))" tickLine={false} axisLine={false} />
                  <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} stroke="hsl(var(--muted-foreground))" tickLine={false} axisLine={false} />
                  <ChartTooltip
                    contentStyle={{ background: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: 12, fontSize: 12 }}
                    labelStyle={{ color: "hsl(var(--muted-foreground))" }}
                  />
                  <Line type="monotone" dataKey="score" stroke="hsl(var(--primary))" strokeWidth={2.5}
                        dot={{ r: 3, fill: "hsl(var(--primary))" }} activeDot={{ r: 5 }} />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Most common mistakes */}
          <Card className="animate-fade-up">
            <CardHeader>
              <CardTitle>Most common mistakes</CardTitle>
              <CardDescription>Top failing rule per session, across all workouts</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {stats.mistakes.length === 0 && (
                <p className="py-6 text-center text-sm text-muted-foreground">No mistakes recorded — clean work.</p>
              )}
              {stats.mistakes.map(([rule, count], i) => (
                <div key={rule} className="space-y-1.5">
                  <div className="flex items-center justify-between text-sm">
                    <span className="font-medium">{titleCase(rule)}</span>
                    <Badge variant={i === 0 ? "destructive" : "warning"}>{count}×</Badge>
                  </div>
                  <div className="h-1.5 overflow-hidden rounded-full bg-muted">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${(count / (stats.mistakes[0]?.[1] ?? 1)) * 100}%` }}
                      transition={{ duration: 0.6, delay: i * 0.08 }}
                      className="h-full rounded-full bg-destructive/70"
                    />
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      )}

      {/* Quick start */}
      {exercises && exercises.length > 0 && (
        <section className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold tracking-tight">Quick start</h2>
            <Button variant="ghost" size="sm" asChild>
              <Link to="/exercises">All exercises <ArrowRight /></Link>
            </Button>
          </div>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {exercises.slice(0, 4).map((ex) => <ExerciseCard key={ex.id} exercise={ex} compact />)}
          </div>
        </section>
      )}

      {/* Recent activity */}
      {!noSessions && (
        <section className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold tracking-tight">Recent activity</h2>
            <Button variant="ghost" size="sm" asChild>
              <Link to="/sessions">View all <ArrowRight /></Link>
            </Button>
          </div>
          <div className="space-y-2">
            {stats.recent.map((s, i) => (
              <motion.div key={s.id} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.04 }}>
                <Link
                  to={`/sessions/${s.id}`}
                  className="flex items-center justify-between gap-3 rounded-xl border border-border/60 bg-card px-4 py-3 transition-colors hover:border-primary/40"
                >
                  <div className="flex min-w-0 items-center gap-3">
                    <span className="grid size-9 shrink-0 place-items-center rounded-lg bg-secondary">
                      <Activity className="size-4 text-primary" />
                    </span>
                    <div className="min-w-0">
                      <p className="truncate text-sm font-medium">{s.exercise}</p>
                      <p className="text-xs text-muted-foreground">{formatDay(s.recorded_at)} · {s.total_reps} reps</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <Badge variant="outline">{s.good_reps}/{s.total_reps} good</Badge>
                    <span className={`text-sm font-bold tabular-nums ${scoreColor(s.score)}`}>{s.score?.toFixed(0) ?? "—"}</span>
                  </div>
                </Link>
              </motion.div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
