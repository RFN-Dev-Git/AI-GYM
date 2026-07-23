import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Camera, Dumbbell, Play, Scan } from "lucide-react";
import type { Exercise } from "@/schemas";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

/** Exercise card for grid and quick-start contexts. */
export function ExerciseCard({ exercise, index = 0, compact = false }: { exercise: Exercise; index?: number; compact?: boolean }) {
  return (
    <motion.article
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: Math.min(index, 8) * 0.05 }}
      className="group relative flex flex-col overflow-hidden rounded-xl border border-border/60 bg-card transition-colors hover:border-primary/40"
    >
      {/* visual header — future image slot with a branded placeholder */}
      <div className={cn("relative flex items-center justify-center overflow-hidden", compact ? "h-20" : "h-28",
        "bg-[radial-gradient(ellipse_at_top,hsl(var(--primary)/0.18),transparent_60%)]")}>
        {exercise.image ? (
          <img src={exercise.image} alt="" className="absolute inset-0 h-full w-full object-cover" />
        ) : (
          <Dumbbell className={cn("text-primary/60 transition-transform duration-300 group-hover:scale-110", compact ? "size-7" : "size-9")} />
        )}
        <Badge
          variant={exercise.camera === "side" ? "primary" : "default"}
          className="absolute right-2.5 top-2.5 gap-1"
        >
          <Camera className="size-3" />
          {exercise.camera === "side" ? "Side view" : "Front view"}
        </Badge>
      </div>

      <div className="flex flex-1 flex-col gap-2 p-4">
        <div>
          <h3 className="font-semibold tracking-tight">{exercise.name}</h3>
          {!compact && <p className="mt-1 line-clamp-2 text-xs leading-relaxed text-muted-foreground">{exercise.description}</p>}
        </div>

        <div className="mt-auto flex flex-wrap gap-1.5">
          {exercise.muscle_groups.slice(0, compact ? 2 : 3).map((m) => (
            <Badge key={m} variant="outline" className="capitalize">{m}</Badge>
          ))}
          <Badge variant="outline" className="gap-1"><Scan className="size-3" />{exercise.rules} checks</Badge>
        </div>

        <Button asChild className="mt-2" size={compact ? "sm" : "default"}>
          <Link to={`/live/${exercise.id}`}><Play />Start session</Link>
        </Button>
      </div>
    </motion.article>
  );
}
