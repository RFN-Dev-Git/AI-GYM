import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "./client";
import type { SessionListItem, SessionReport } from "@/schemas";

export function useSessions() {
  return useQuery({
    queryKey: ["sessions"],
    queryFn: () => api.get<SessionListItem[]>("/api/sessions"),
  });
}

export function useSession(sessionId: string | undefined) {
  return useQuery({
    queryKey: ["sessions", "report", sessionId],
    queryFn: () => api.get<SessionReport>(`/api/sessions/${sessionId}`),
    enabled: Boolean(sessionId),
  });
}

export function useDeleteSession() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (sessionId: string) => api.delete(`/api/sessions/${sessionId}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["sessions"] }),
  });
}

/**
 * Download the exported session report as a pretty-printed JSON file.
 * Uses the existing GET contract unchanged — the "download" is a client-side
 * Blob; the API itself gains no new endpoint.
 */
export async function downloadSessionReport(sessionId: string, fileHint = "session"): Promise<void> {
  const report = await api.get<SessionReport>(`/api/sessions/${sessionId}`);
  const blob = new Blob([JSON.stringify(report, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  const safe = fileHint.replace(/[^\w.-]+/g, "_").replace(/^_+|_+$/g, "") || "session";
  a.href = url;
  a.download = `${safe}_${sessionId}.json`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}
