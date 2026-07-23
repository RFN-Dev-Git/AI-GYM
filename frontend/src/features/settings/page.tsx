import { useEffect, useState } from "react";
import { Moon, Save, Settings2, Sun, Video } from "lucide-react";
import { useSettings, useUpdateSettings } from "@/lib/api/settings";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/shared";
import { useTheme } from "@/providers/theme";
import { useToast } from "@/providers/toast";
import { cn } from "@/lib/utils";

function Toggle({
  checked,
  onChange,
  label,
  hint,
}: {
  checked: boolean;
  onChange: (v: boolean) => void;
  label: string;
  hint?: string;
}) {
  return (
    <button
      type="button"
      onClick={() => onChange(!checked)}
      className="flex w-full items-center justify-between gap-4 rounded-lg border border-border/60 bg-card px-4 py-3 text-left transition-colors hover:border-primary/30"
    >
      <span>
        <span className="block text-sm font-medium">{label}</span>
        {hint && <span className="mt-0.5 block text-xs text-muted-foreground">{hint}</span>}
      </span>
      <span
        aria-checked={checked}
        role="switch"
        className={cn(
          "relative h-6 w-11 shrink-0 rounded-full transition-colors",
          checked ? "bg-primary" : "bg-muted",
        )}
      >
        <span
          className={cn(
            "absolute top-0.5 size-5 rounded-full bg-white shadow transition-all",
            checked ? "left-[22px]" : "left-0.5",
          )}
        />
      </span>
    </button>
  );
}

function Field({
  label,
  hint,
  value,
  onChange,
  type = "text",
}: {
  label: string;
  hint?: string;
  value: string;
  onChange: (v: string) => void;
  type?: string;
}) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-sm font-medium">{label}</span>
      <Input type={type} value={value} onChange={(e) => onChange(e.target.value)} />
      {hint && <span className="mt-1 block text-xs text-muted-foreground">{hint}</span>}
    </label>
  );
}

/** Keys rendered in the form, grouped (order = presentation order). */
const EDITABLE: { key: string; label: string; hint: string; kind: "bool" | "text" | "number" | "path"; section: "capture" | "output" | "analytics" }[] = [
  { key: "USE_WEBCAM", label: "Use webcam by default", hint: "Off = analyze a video file from disk", kind: "bool", section: "capture" },
  { key: "WEBCAM_INDEX", label: "Webcam index", hint: "0 is usually the built-in camera", kind: "number", section: "capture" },
  { key: "VIDEO_PATH", label: "Video path (CLI/dev)", hint: "Engine CLI fallback when the webcam is off — the web app uploads videos instead", kind: "path", section: "capture" },
  { key: "MODEL_PATH", label: "Pose model", hint: "BlazePose .task file", kind: "path", section: "capture" },
  { key: "SAVE_OUTPUT", label: "Save annotated video", hint: "Write the rendered session to disk", kind: "bool", section: "output" },
  { key: "OUTPUT_PATH", label: "Output video path", hint: "Where annotated videos go", kind: "path", section: "output" },
  { key: "ANALYTICS_FPS", label: "Analytics FPS", hint: "Frame rate used for rep timing", kind: "number", section: "analytics" },
  { key: "EXPORT_SESSION", label: "Export session reports", hint: "Write a JSON report after engine CLI runs", kind: "bool", section: "analytics" },
];

export function SettingsPage() {
  const { data, isLoading, isError, refetch } = useSettings();
  const update = useUpdateSettings();
  const { theme, toggle } = useTheme();
  const { push } = useToast();
  const [form, setForm] = useState<Record<string, string | boolean>>({});
  const [dirty, setDirty] = useState(false);

  useEffect(() => {
    if (data && !dirty) {
      setForm(
        Object.fromEntries(
          EDITABLE.map(({ key, kind }) => [key, kind === "bool" ? Boolean(data[key]) : String(data[key] ?? "")]),
        ),
      );
    }
  }, [data, dirty]);

  if (isLoading) {
    return <div className="space-y-4"><Skeleton className="h-8 w-40" />{[1, 2, 3].map((i) => <Skeleton key={i} className="h-48" />)}</div>;
  }
  if (isError) {
    return (
      <EmptyState icon={Settings2} title="Backend unreachable" hint="Start the API, then retry."
        action={<Button onClick={() => refetch()}>Retry</Button>} />
    );
  }

  const set = (key: string, value: string | boolean) => {
    setForm((f) => ({ ...f, [key]: value }));
    setDirty(true);
  };

  const save = () => {
    const patch: Record<string, unknown> = {};
    for (const { key, kind } of EDITABLE) {
      const raw = form[key];
      if (raw === undefined) continue;
      if (kind === "bool") patch[key] = Boolean(raw);
      else if (kind === "number") patch[key] = Number(raw);
      else patch[key] = raw === "" ? null : raw;
    }
    Object.keys(patch).forEach((k) => patch[k] === null && delete patch[k]);
    update.mutate(patch as never, {
      onSuccess: () => {
        push("Settings saved");
        setDirty(false);
      },
      onError: (e) => push(e.message, "error"),
    });
  };

  const sections = [
    { id: "capture", title: "Capture", icon: Video, description: "Which camera or video feeds the coach" },
    { id: "output", title: "Output", icon: Save, description: "Annotated video rendering" },
    { id: "analytics", title: "Analytics", icon: Settings2, description: "Session statistics engine" },
  ] as const;

  return (
    <div className="space-y-6">
      <header className="flex items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Settings</h1>
          <p className="text-sm text-muted-foreground">Persisted to the backend configuration (.env).</p>
        </div>
        <Button onClick={save} disabled={!dirty || update.isPending}>
          <Save /> {update.isPending ? "Saving…" : "Save changes"}
        </Button>
      </header>

      {/* Appearance (frontend-only preference) */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            {theme === "dark" ? <Moon className="size-4 text-primary" /> : <Sun className="size-4 text-primary" />}
            Appearance
          </CardTitle>
          <CardDescription>Stored locally on this device</CardDescription>
        </CardHeader>
        <CardContent>
          <Toggle
            checked={theme === "dark"}
            onChange={toggle}
            label="Dark mode"
            hint="AI-GYM is designed dark-first"
          />
        </CardContent>
      </Card>

      {sections.map((section) => (
        <Card key={section.id}>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <section.icon className="size-4 text-primary" /> {section.title}
            </CardTitle>
            <CardDescription>{section.description}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {EDITABLE.filter((f) => f.section === section.id).map((f) =>
              f.kind === "bool" ? (
                <Toggle
                  key={f.key}
                  checked={Boolean(form[f.key])}
                  onChange={(v) => set(f.key, v)}
                  label={f.label}
                  hint={f.hint}
                />
              ) : (
                <Field
                  key={f.key}
                  label={f.label}
                  hint={f.hint}
                  type={f.kind === "number" ? "number" : "text"}
                  value={String(form[f.key] ?? "")}
                  onChange={(v) => set(f.key, v)}
                />
              ),
            )}
          </CardContent>
        </Card>
      ))}

      <p className="text-xs text-muted-foreground">
        Note: exercise rules, thresholds and counting behaviour are code (in the backend) and intentionally not
        editable here — they are the product's source of truth.
      </p>
    </div>
  );
}
