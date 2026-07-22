import { lazy, Suspense } from "react";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { AppShell } from "@/components/layout/app-shell";
import { Skeleton } from "@/components/ui/skeleton";
import { ExercisesPage } from "@/features/exercises/page";
import { LivePage } from "@/features/live/page";
import { HistoryPage } from "@/features/history/page";
import { SettingsPage } from "@/features/settings/page";
import { NotFoundPage } from "@/features/not-found";

// Chart-heavy pages (recharts) are code-split so the landing bundle stays lean.
const DashboardPage = lazy(() =>
  import("@/features/dashboard/page").then((m) => ({ default: m.DashboardPage })),
);
const ReportPage = lazy(() =>
  import("@/features/report/page").then((m) => ({ default: m.ReportPage })),
);

function PageFallback() {
  return (
    <div className="space-y-4">
      <Skeleton className="h-8 w-56" />
      <Skeleton className="h-40" />
      <Skeleton className="h-64" />
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppShell />}>
          <Route index element={
            <Suspense fallback={<PageFallback />}><DashboardPage /></Suspense>
          } />
          <Route path="exercises" element={<ExercisesPage />} />
          <Route path="live/:exerciseId" element={<LivePage />} />
          <Route path="sessions" element={<HistoryPage />} />
          <Route path="sessions/:sessionId" element={
            <Suspense fallback={<PageFallback />}><ReportPage /></Suspense>
          } />
          <Route path="settings" element={<SettingsPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
