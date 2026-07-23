import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "./client";
import type { AppSettings, SettingsPatch } from "@/schemas";

export function useSettings() {
  return useQuery({
    queryKey: ["settings"],
    queryFn: () => api.get<AppSettings>("/api/settings"),
  });
}

export function useUpdateSettings() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (patch: SettingsPatch) => api.put<AppSettings>("/api/settings", patch),
    onSuccess: (data) => qc.setQueryData(["settings"], data),
  });
}
