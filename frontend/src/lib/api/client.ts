/** Tiny fetch wrapper — one place for base URL handling and error typing. */

/** One FastAPI validation issue item (pydantic v2 shape). */
interface ValidationIssue {
  loc?: (string | number)[];
  msg?: string;
  type?: string;
}

/**
 * Extract a human-readable message from ANY FastAPI error body.
 *
 * FastAPI emits `detail` in two shapes:
 *   • string  — raised HTTPException("...") / HTTPException(detail="...")
 *   • array   — pydantic request validation errors: [{loc, msg, type}, ...]
 * Rendering the raw array is the classic "[object Object]" toast; here each
 * issue becomes `body.file: Field required` and all issues are joined.
 */
export function errorDetailMessage(status: number, statusText: string, body: unknown): string {
  const detail = (body as { detail?: unknown } | null)?.detail;
  if (typeof detail === "string" && detail.trim()) return detail;
  if (Array.isArray(detail) && detail.length > 0) {
    return detail
      .map((issue: ValidationIssue) => {
        const where = Array.isArray(issue.loc) ? issue.loc.join(".") : "";
        return where && issue.msg ? `${where}: ${issue.msg}` : issue.msg ?? JSON.stringify(issue);
      })
      .join("; ");
  }
  return statusText || `Request failed (${status})`;
}

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    /** Raw parsed error body — kept for debugging (console), never for display. */
    public details?: unknown,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

/** Parse a response/error body once, tolerating non-JSON replies. */
async function parseBody(res: Response): Promise<unknown> {
  try {
    return await res.json();
  } catch {
    return undefined; /* non-JSON error body */
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const body = await parseBody(res);
    throw new ApiError(res.status, errorDetailMessage(res.status, res.statusText, body), body);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  put: <T>(path: string, body: unknown) =>
    request<T>(path, { method: "PUT", body: JSON.stringify(body) }),
  delete: (path: string) => request<void>(path, { method: "DELETE" }),
};
