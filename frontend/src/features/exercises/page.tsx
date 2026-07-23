import { useMemo, useState } from "react";
import { Dumbbell, Search, Video } from "lucide-react";
import { useExercises } from "@/lib/api/exercises";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/shared";
import { ExerciseCard } from "./exercise-card";
import { cn } from "@/lib/utils";

const CAMERA_FILTERS = [
  { id: "all", label: "All" },
  { id: "side", label: "Side view" },
  { id: "both", label: "Front view" },
] as const;

export function ExercisesPage() {
  const { data: exercises, isLoading, isError, refetch } = useExercises();
  const [query, setQuery] = useState("");
  const [camera, setCamera] = useState<string>("all");
  const [muscle, setMuscle] = useState<string | null>(null);

  const muscles = useMemo(
    () => [...new Set((exercises ?? []).flatMap((e) => e.muscle_groups))].sort(),
    [exercises],
  );

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return (exercises ?? []).filter((e) => {
      if (camera !== "all" && e.camera !== camera) return false;
      if (muscle && !e.muscle_groups.includes(muscle)) return false;
      if (!q) return true;
      return (
        e.name.toLowerCase().includes(q) ||
        e.description.toLowerCase().includes(q) ||
        e.muscle_groups.some((m) => m.toLowerCase().includes(q))
      );
    });
  }, [exercises, query, camera, muscle]);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-48" />
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-52" />)}
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <EmptyState icon={Video} title="Backend unreachable"
        hint="Start the API (make backend from the repo root), then retry."
        action={<button className="text-sm text-primary underline" onClick={() => refetch()}>Retry</button>}
      />
    );
  }

  return (
    <div className="space-y-6">
      <header className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Exercises</h1>
          <p className="text-sm text-muted-foreground">
            {filtered.length} of {exercises?.length ?? 0} coached movements
          </p>
        </div>
        <div className="relative w-full sm:w-72">
          <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search exercises or muscles…"
            className="pl-9"
          />
        </div>
      </header>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-2">
        {CAMERA_FILTERS.map((f) => (
          <button
            key={f.id}
            onClick={() => setCamera(f.id)}
            className={cn(
              "rounded-full border px-3 py-1.5 text-xs font-medium transition-colors",
              camera === f.id
                ? "border-primary/60 bg-primary/15 text-primary"
                : "border-border bg-card text-muted-foreground hover:text-foreground",
            )}
          >
            {f.label}
          </button>
        ))}
        <span className="mx-1 hidden h-5 w-px bg-border sm:block" />
        <Badge
          variant={muscle === null ? "primary" : "outline"}
          className="cursor-pointer"
          onClick={() => setMuscle(null)}
        >
          All muscles
        </Badge>
        {muscles.map((m) => (
          <Badge
            key={m}
            variant={muscle === m ? "primary" : "outline"}
            className="cursor-pointer capitalize"
            onClick={() => setMuscle((cur) => (cur === m ? null : m))}
          >
            {m}
          </Badge>
        ))}
      </div>

      {filtered.length === 0 ? (
        <EmptyState icon={Dumbbell} title="No matches" hint="Try a different search or clear the filters." />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map((e, i) => (
            <ExerciseCard key={e.id} exercise={e} index={i} />
          ))}
        </div>
      )}
    </div>
  );
}
