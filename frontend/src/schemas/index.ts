/** Typed models mirroring backend responses — the single coupling seam.
 *
 * These interfaces describe the exported session-report JSON exactly as the
 * Python backend produces it. When the backend changes, this file changes
 * first; feature code never talks about raw shapes.
 */

// ── Exercise catalogue ──────────────────────────────────────────────────────
export interface Exercise {
  id: string;
  name: string;
  description: string;
  muscle_groups: string[];
  camera: "side" | "both" | string;
  counters: string[];
  rules: number;
  /** Forward slot for real thumbnails (null today). */
  image: string | null;
}

// ── Session report (as exported by the backend) ─────────────────────────────
export interface SessionInfo {
  id: string;
  recorded_at: string;
  fps: number;
  scoring: { base_score: number; severity_weights: Record<string, number> };
}

export interface CounterRule {
  name: string;
  joints: number[];
  up_angle: number;
  down_angle: number;
  up_stage: string;
  down_stage: string;
  min_rom_angle: number | null;
  max_rom_angle: number | null;
  min_rep_frames: number;
  sync_group: string | null;
}

export interface ExerciseInfo {
  name: string;
  description: string;
  muscle_groups: string[];
  camera: string;
  counter_rules: CounterRule[];
}

export interface RuleDefinition {
  name: string;
  type: "angle" | "range_of_motion" | "distance" | "counter" | string;
  severity: "error" | "warning" | "info" | string;
  message: string;
  expected_min: number | null;
  expected_max: number | null;
  value_unit: "degrees" | "ratio" | null;
  joints?: number[];
  measurement?: number[];
  reference?: number[];
}

export interface RepEvaluation {
  rule: string;
  passed: boolean;
  measured_value: number | null;
  message?: string;
}

export type JudgedBy = "completion" | "rules" | "counter";

export interface Repetition {
  number: number;
  good: boolean;
  judged_by: JudgedBy;
  score: number;
  start_frame: number | null;
  end_frame: number | null;
  duration_seconds: number | null;
  start_time: number | null;
  end_time: number | null;
  evaluations: RepEvaluation[];
}

export interface SessionSummary {
  total_reps: number;
  good_reps: number;
  bad_reps: number;
  accuracy: number;
  average_rep_duration: number;
  fastest_rep: number;
  slowest_rep: number;
  total_workout_duration: number;
  common_errors: Record<string, number>;
  most_common_error: string | null;
  score: number | null;
}

export interface RuleStats {
  rule: string;
  evaluations: number;
  passed: number;
  failed: number;
  success_rate: number | null;
  avg_measured_value: number | null;
  min_measured_value: number | null;
  max_measured_value: number | null;
}

export interface SessionStats {
  rules: RuleStats[];
  scores: { best: number | null; worst: number | null; std_dev: number | null };
}

/** Full report document. `session`/`stats` are absent in pre-v4 exports. */
export interface SessionReport {
  session?: SessionInfo;
  exercise: ExerciseInfo;
  summary: SessionSummary;
  rules: RuleDefinition[];
  history: Repetition[];
  stats?: SessionStats;
}

// ── History list ────────────────────────────────────────────────────────────
export interface SessionListItem {
  id: string;
  file: string;
  exercise: string;
  recorded_at: string | null;
  total_reps: number;
  good_reps: number;
  accuracy: number;
  score: number | null;
  duration: number;
  most_common_error: string | null;
}

// ── Settings ────────────────────────────────────────────────────────────────
export type AppSettings = Record<string, string | number | boolean>;
export type SettingsPatch = Partial<{
  USE_WEBCAM: boolean;
  WEBCAM_INDEX: number;
  VIDEO_PATH: string;
  MODEL_PATH: string;
  SAVE_OUTPUT: boolean;
  OUTPUT_PATH: string;
  ANALYTICS_FPS: number;
  DISPLAY_MAX_WIDTH: number;
  EXPORT_SESSION: boolean;
  USE_3D: boolean;
  ENABLE_SMOOTHING: boolean;
}>;

// ── Uploads (web-app video workflow) ────────────────────────────────────────
/** An uploaded workout video (POST response; `uploaded_at` on list only). */
export interface UploadInfo {
  id: string;
  name: string;
  size: number;
  uploaded_at?: string;
}

// ── Live stream ─────────────────────────────────────────────────────────────
export interface LiveRuleState {
  name: string;
  passed: boolean;
  severity: string;
  message: string;
  value: number | null;
  is_3d?: boolean;
}

export interface LiveState {
  type: "state";
  exercise: string;
  elapsed: number;
  fps: number;
  reps: number;
  good: number;
  bad: number;
  stage: string;
  angle: number;
  last_rep: "good" | "bad" | null;
  live_score: number | null;
  side: string | null;
  adapting: boolean;
  is_3d?: boolean;
  feedback: string[];
  rules: LiveRuleState[];
}

export interface LiveEnd {
  type: "end";
  reps: number;
  session_id?: string;
  export_error?: string;
  /** Filename of the rendered session video (when SAVE_OUTPUT is enabled). */
  rendered_video?: string;
  rendered_error?: string;
  is_3d?: boolean;
}

export interface LiveError {
  type: "error";
  message: string;
}

export type LiveMessage = LiveState | LiveEnd | LiveError;
