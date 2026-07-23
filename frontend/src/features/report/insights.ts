import type { Repetition, RuleDefinition, RuleStats, SessionSummary } from "@/schemas";

/**
 * Pure report derivations — no React, no IO.
 *
 * Everything the redesigned report renders is computed here from the
 * exported session JSON (the single source of truth): understandable summary
 * wording, coaching recommendations, measurement-gauge geometry, the workout
 * timeline, best/worst selection, and the score-progression series.
 */

// ── Form rating (renames the engine score into human language) ──────────────
export interface FormRating {
  label: string;
  tone: "success" | "warning" | "destructive" | "muted";
}

/** Bands deliberately mirror the brand's scoreColor thresholds (80 / 50). */
export function scoreRating(score: number | null): FormRating {
  if (score == null) return { label: "Unscored", tone: "muted" };
  if (score >= 80) return { label: "Excellent", tone: "success" };
  if (score >= 50) return { label: "Needs polish", tone: "warning" };
  return { label: "Needs work", tone: "destructive" };
}

/**
 * Rep verdicts — the honest rename of "accuracy": the share of reps that
 * passed every form check. Presented as "8 of 10 reps", never as a bare %.
 */
export interface VerdictShare {
  good: number;
  bad: number;
  total: number;
  pct: number | null;
}

export function verdictShare(summary: SessionSummary): VerdictShare {
  const { good_reps: good, bad_reps: bad, total_reps: total } = summary;
  return { good, bad, total, pct: total > 0 ? (good / total) * 100 : null };
}

// ── Units ────────────────────────────────────────────────────────────────────
export function formatMeasured(value: number | null | undefined, unit: string | null | undefined): string {
  if (value == null) return "—";
  if (unit === "degrees") return `${value.toFixed(0)}°`;
  if (unit === "ratio") return `${value.toFixed(2)}×`;
  return Number.isInteger(value) ? String(value) : value.toFixed(1);
}

/** Expected range in user terms: "60–170°", "≥ 1.20×", "≤ 170°", "—". */
export function rangeText(
  min: number | null | undefined,
  max: number | null | undefined,
  unit: string | null | undefined,
): string {
  const u = unit === "degrees" ? "°" : unit === "ratio" ? "×" : "";
  if (min != null && max != null) return `${min}–${max}${u}`;
  if (min != null) return `≥ ${min}${u}`;
  if (max != null) return `≤ ${max}${u}`;
  return "—";
}

// ── Measurement gauge geometry ──────────────────────────────────────────────
export interface GaugeGeometry {
  domainMin: number;
  domainMax: number;
  /** Position (0–100 %) of the expected-range edges; null when unbounded. */
  loPct: number | null;
  hiPct: number | null;
  /** Position of the measured value; null when no value. */
  posPct: number | null;
  inRange: boolean | null;
}

/**
 * Map expected bounds + measured value onto a padded 0–100 % domain with
 * 35 % breathing room on each side. Null-safe per field; both bounds absent
 * → null (nothing meaningful to draw).
 */
export function gaugeGeometry(
  min: number | null | undefined,
  max: number | null | undefined,
  value: number | null | undefined,
): GaugeGeometry | null {
  const lo = min ?? null;
  const hi = max ?? null;
  if (lo == null && hi == null) return null;
  const ref = [lo, hi, value ?? null].filter((v): v is number => v != null);
  let dMin = Math.min(...ref);
  let dMax = Math.max(...ref);
  if (dMax - dMin < 1e-6) {
    dMin -= 1;
    dMax += 1;
  }
  const pad = (dMax - dMin) * 0.35;
  dMin -= pad;
  dMax += pad;
  const pct = (v: number) => Math.max(0, Math.min(100, ((v - dMin) / (dMax - dMin)) * 100));
  const inRange =
    value == null ? null : (lo == null || value >= lo) && (hi == null || value <= hi);
  return {
    domainMin: dMin,
    domainMax: dMax,
    loPct: lo == null ? null : pct(lo),
    hiPct: hi == null ? null : pct(hi),
    posPct: value == null ? null : pct(value),
    inRange,
  };
}

// ── Coaching recommendations ────────────────────────────────────────────────
interface TipRule {
  pattern: RegExp;
  tip: string;
}

/**
 * Corrective coaching keyed off rule names — grounded in the engine's real
 * rule vocabulary (messages already state WHAT; these state HOW TO FIX).
 * Ordered: first match wins. Data-driven exercises fall through to the
 * generic range-based advice below.
 */
const TIP_RULES: TipRule[] = [
  {
    pattern: /elbow_too_tight|curl/i,
    tip: "Control the squeeze at the top: stop the curl before the elbow closes fully, and lower the weight all the way down instead of bouncing out of the bottom.",
  },
  {
    pattern: /hyperextend|locking|unlocked|lock/i,
    tip: "Keep a soft bend at lockout — stop just short of fully straightening the joint and keep tension on the muscle rather than resting on the joint.",
  },
  {
    pattern: /drift/i,
    tip: "Pin the upper arm to your ribs — imagine holding a card in your armpit. If the elbow still travels forward, the weight is too heavy: drop it and isolate.",
  },
  {
    pattern: /knee.*(align|track)|valgus|aligned/i,
    tip: "Drive the knees outward so they track over the second toe — screw your feet into the floor and feel the glutes switch on before you descend.",
  },
  {
    pattern: /knee|squat|depth/i,
    tip: "Own the full range: descend under control until you reach the target angle, then drive up without cutting the rep short. Reduce the load until the full depth feels stable.",
  },
  {
    pattern: /back|torso|spine|lean|chest_up/i,
    tip: "Brace your core before every rep and keep a neutral spine — chest tall, shoulders packed down, hinge from the hips rather than rounding the lower back.",
  },
  {
    pattern: /neck|head/i,
    tip: "Keep your neck packed and neutral: eyes on the floor a step ahead, chin tucked so the spine stays one straight line from head to hips.",
  },
  {
    pattern: /shoulder.*rom|rom.*shoulder/i,
    tip: "Press all the way to full overhead extension and control the weight back down every rep — partial range usually means the load is too heavy, so drop it until you own the whole arc.",
  },
  {
    pattern: /pull|lat/i,
    tip: "Pull the bar to your upper chest on every rep and lead with the elbows. If you can't reach your chest without swinging, reduce the weight and slow the rep down.",
  },
  {
    pattern: /wrist|grip|distance/i,
    tip: "Set your grip before you unrack: hands wider than shoulder width, wrists stacked over elbows and straight under the bar.",
  },
  {
    pattern: /tempo|speed|duration|counter|rom/i,
    tip: "Slow the rep down — about two seconds up and two seconds down with a brief pause at each end. Full control beats more reps.",
  },
];

/**
 * Actionable recommendation for a failing rule: personalized with the
 * user's measured average and the target range when known, then either a
 * curated technique tip (keyword-matched) or a generic range-based one.
 */
export function recommendationFor(rule: RuleDefinition, avgMeasured?: number | null): string {
  const matched = TIP_RULES.find((t) => t.pattern.test(rule.name));
  const tip =
    matched?.tip ??
    "Focus your next set on this single check — film yourself, watch the moment you leave the target zone, and drill one slow, perfect rep before speeding up.";
  const target = rangeText(rule.expected_min, rule.expected_max, rule.value_unit);
  if (avgMeasured != null && target !== "—") {
    const measured = formatMeasured(avgMeasured, rule.value_unit);
    return `Your failing reps averaged ${measured} (target ${target}). ${tip}`;
  }
  if (target !== "—") return `Target ${target} on every rep. ${tip}`;
  return tip;
}

// ── Compact coaching (short UI slots — one scannable line each) ─────────────
const SHORT_TIPS: TipRule[] = [
  { pattern: /elbow_too_tight|curl/i, tip: "Stop the curl before the elbow closes fully." },
  { pattern: /hyperextend|locking|unlocked|lock/i, tip: "Keep a soft bend at lockout — never snap it straight." },
  { pattern: /drift/i, tip: "Pin your upper arm to your ribs throughout." },
  { pattern: /knee.*(align|track)|valgus|aligned/i, tip: "Push knees out over the second toe on every rep." },
  { pattern: /knee|squat|depth/i, tip: "Hit full depth, then drive up — don't cut reps short." },
  { pattern: /back|torso|spine|lean|chest_up/i, tip: "Brace your core, chest tall, hinge from the hips." },
  { pattern: /neck|head/i, tip: "Keep your neck neutral — eyes down, chin tucked." },
  { pattern: /shoulder.*rom|rom.*shoulder/i, tip: "Press fully overhead; control the whole arc down." },
  { pattern: /pull|lat/i, tip: "Pull to your upper chest, leading with the elbows." },
  { pattern: /wrist|grip|distance/i, tip: "Grip wider than shoulder width before you unrack." },
  { pattern: /tempo|speed|duration|counter|rom/i, tip: "Slow down — own every inch of the range." },
];

/** One-line imperative fix for compact slots (falls back to the rule's cue). */
export function tipShortFor(rule: RuleDefinition): string {
  return (
    SHORT_TIPS.find((t) => t.pattern.test(rule.name))?.tip ??
    rule.message ??
    "Focus on this check next set."
  );
}

/** Compact "avg 175° · target 60–170°" line (null when nothing to quantify). */
export function avgTargetText(rule: RuleDefinition, avg: number | null | undefined): string | null {
  const target = rangeText(rule.expected_min, rule.expected_max, rule.value_unit);
  if (target === "—") return null;
  if (avg == null) return `target ${target}`;
  return `avg ${formatMeasured(avg, rule.value_unit)} · target ${target}`;
}

/** One failing rule, enriched for the coaching panel. */
export interface CoachingItem {
  name: string;
  def: RuleDefinition | null;
  failed: number;
  evaluations: number | null;
  successRate: number | null;
  avgMeasured: number | null;
  tip: string;
}

export interface CoachingModel {
  items: CoachingItem[]; // failing rules, worst first
  passing: string[]; // rule names that never failed
  fromStats: boolean; // false = legacy export fallback (counts only)
}

export function buildCoaching(
  rules: RuleDefinition[],
  stats: RuleStats[] | null | undefined,
  commonErrors: Record<string, number>,
): CoachingModel {
  const defs = new Map(rules.map((r) => [r.name, r]));
  if (stats) {
    const failing = stats.filter((s) => s.failed > 0).sort((a, b) => b.failed - a.failed);
    const passing = stats.filter((s) => s.failed === 0).map((s) => s.rule);
    return {
      items: failing.map((s) => {
        const def = defs.get(s.rule) ?? null;
        return {
          name: s.rule,
          def,
          failed: s.failed,
          evaluations: s.evaluations,
          successRate: s.success_rate,
          avgMeasured: s.avg_measured_value,
          tip: def
            ? recommendationFor(def, s.avg_measured_value)
            : "This check failed in the session — review it in your next set.",
        };
      }),
      passing,
      fromStats: true,
    };
  }
  // Older export without aggregated stats: counts only, no averages.
  const names = Object.entries(commonErrors).sort((a, b) => b[1] - a[1]);
  return {
    items: names.map(([name, failed]) => {
      const def = defs.get(name) ?? null;
      return {
        name,
        def,
        failed,
        evaluations: null,
        successRate: null,
        avgMeasured: null,
        tip: def ? recommendationFor(def, null) : "This check failed in the session — review it in your next set.",
      };
    }),
    passing: [],
    fromStats: false,
  };
}

// ── Best / worst reps ───────────────────────────────────────────────────────
export interface BestWorst {
  best: Repetition;
  worst: Repetition;
  average: number;
  single: boolean;
}

export function pickBestWorst(history: Repetition[]): BestWorst | null {
  if (history.length === 0) return null;
  const average = history.reduce((a, r) => a + r.score, 0) / history.length;
  let best = history[0];
  let worst = history[0];
  for (const rep of history) {
    if (rep.score > best.score) best = rep;
    if (rep.score < worst.score) worst = rep;
  }
  return { best, worst, average, single: history.length === 1 };
}

// ── Score progression series ────────────────────────────────────────────────
export interface ProgressPoint {
  rep: number;
  score: number;
  good: boolean;
  duration: number | null;
  failed: number;
}

export interface Progression {
  points: ProgressPoint[];
  average: number | null;
}

export function buildProgression(history: Repetition[]): Progression {
  const points = history.map((r) => ({
    rep: r.number,
    score: Math.round(r.score),
    good: r.good,
    duration: r.duration_seconds,
    failed: r.evaluations.filter((e) => !e.passed).length,
  }));
  return {
    points,
    average: points.length ? points.reduce((a, p) => a + p.score, 0) / points.length : null,
  };
}

// ── Y-axis domain for the score-progression chart ───────────────────────────
const AXIS_PAD_RATIO = 0.15; // breathing room relative to the observed range
const AXIS_PAD_MIN = 5; // points — always leave ≥ this much headroom
const AXIS_SPAN_MIN = 20; // points — never zoom tighter (stays honest/legible)
const AXIS_SNAP = 5; // outward snap so gridlines/ticks stay round

/**
 * Y-axis domain for the score-per-repetition chart, derived from the data.
 * A fixed [0, 100] scale flattens small rep-to-rep changes, so the domain
 * hugs the observed scores with a little padding — while staying honest:
 * - pad = max(15% of the range, 5 points) above and below the data;
 * - never zooms tighter than a 20-point window (tiny wiggles must not fill
 *   the chart) — expanded symmetrically around the data midpoint;
 * - lower bound floored at 0 when every score is non-negative (lower values
 *   are impossible for engine scores) — real negative data is never hidden;
 * - never clamps at 100: explicit rep scores may legitimately exceed it;
 * - snapped outward to 5-point gridlines so ticks stay round and stable;
 * - as a hard invariant the domain always contains every score (no clipping).
 */
export function scoreAxisDomain(scores: number[]): [number, number] {
  const valid = scores.filter((s) => Number.isFinite(s));
  if (valid.length === 0) return [0, 100];
  const lo = Math.min(...valid);
  const hi = Math.max(...valid);
  const pad = Math.max((hi - lo) * AXIS_PAD_RATIO, AXIS_PAD_MIN);
  let min = lo - pad;
  let max = hi + pad;
  if (max - min < AXIS_SPAN_MIN) {
    const mid = (lo + hi) / 2;
    min = mid - AXIS_SPAN_MIN / 2;
    max = mid + AXIS_SPAN_MIN / 2;
  }
  // Re-apply the absolute headroom after any symmetric expansion.
  min = Math.min(min, lo - AXIS_PAD_MIN);
  max = Math.max(max, hi + AXIS_PAD_MIN);
  if (min < 0 && lo >= 0) min = 0; // impossible values — but never hide data
  return [Math.floor(min / AXIS_SNAP) * AXIS_SNAP, Math.ceil(max / AXIS_SNAP) * AXIS_SNAP];
}

// ── Workout timeline ────────────────────────────────────────────────────────
export interface TimelineSegment {
  kind: "rep" | "gap";
  /** Share of total session time (0–1). */
  span: number;
  rep?: Repetition;
  start: number; // seconds
  end: number; // seconds
}

export interface TimelineModel {
  segments: TimelineSegment[];
  duration: number;
  ticks: number[]; // seconds at 0/25/50/75/100 %
}

/**
 * Convert rep frame numbers to seconds and lay reps + rest gaps along the
 * session duration. Returns null when the export lacks frame timing (older
 * files or missing fps) so the UI can downgrade gracefully.
 * Now prefers start_time/end_time if available (new 3D reports), fallback to frames.
 */
export function buildTimeline(
  history: Repetition[],
  fps: number | null | undefined,
  totalDuration: number | null | undefined,
): TimelineModel | null {
  if (history.length === 0) return null;
  const hasTime = history.some((r) => r.start_time != null && r.end_time != null);
  if (!hasTime && (!fps || fps <= 0)) return null;
  if (!hasTime && history.some((r) => r.start_frame == null || r.end_frame == null)) return null;
  const segments: TimelineSegment[] = [];
  let cursor = 0;
  for (const rep of history) {
    let start: number;
    let end: number;
    if (rep.start_time != null && rep.end_time != null) {
      start = rep.start_time;
      end = Math.max(rep.end_time, start);
    } else if (rep.start_frame != null && rep.end_frame != null && fps) {
      start = rep.start_frame / fps;
      end = Math.max(rep.end_frame / fps, start);
    } else {
      continue;
    }
    if (start - cursor > 0.05) {
      segments.push({ kind: "gap", span: 0, start: cursor, end: start });
    }
    segments.push({ kind: "rep", span: 0, rep, start, end });
    cursor = Math.max(cursor, end);
  }
  const duration = Math.max(totalDuration ?? 0, cursor);
  if (duration <= 0) return null;
  for (const seg of segments) seg.span = (seg.end - seg.start) / duration;
  if (cursor < duration) segments.push({ kind: "gap", span: (duration - cursor) / duration, start: cursor, end: duration });
  return { segments, duration, ticks: [0, 0.25, 0.5, 0.75, 1].map((f) => f * duration) };
}
