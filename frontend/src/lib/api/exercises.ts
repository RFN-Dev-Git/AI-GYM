import { useQuery } from "@tanstack/react-query";
import { api } from "./client";
import type { Exercise } from "@/schemas";

export function useExercises() {
  return useQuery({
    queryKey: ["exercises"],
    queryFn: () => api.get<Exercise[]>("/api/exercises"),
    staleTime: 5 * 60_000, // catalogue is static per deploy
  });
}
