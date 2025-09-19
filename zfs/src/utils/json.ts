/**
 * Pulls out the most likely JSON object/array from a mixed stdout string.
 * Returns a JSON string (so existing JSON.parse call sites can stay unchanged).
 */
export function sanitizeRawJson(raw: string, fallback = "[]"): string {
    const text = (raw ?? "").trim();
    if (!text) return fallback;

    const firstObj = text.indexOf("{");
    const firstArr = text.indexOf("[");
    const starts = [firstObj, firstArr].filter(i => i >= 0);
    if (!starts.length) return fallback;

    const first = Math.min(...starts);
    let candidate = text.slice(first).trim();

    const lastBrace = candidate.lastIndexOf("}");
    const lastBracket = candidate.lastIndexOf("]");
    const last = Math.max(lastBrace, lastBracket);
    if (last >= 0) candidate = candidate.slice(0, last + 1);

    try {
        JSON.parse(candidate);
        return candidate;
    } catch {
        const lastStart = Math.max(text.lastIndexOf("{"), text.lastIndexOf("["));
        if (lastStart >= 0) {
            let c2 = text.slice(lastStart).trim();
            const lb2 = c2.lastIndexOf("}");
            const la2 = c2.lastIndexOf("]");
            const l2 = Math.max(lb2, la2);
            if (l2 >= 0) c2 = c2.slice(0, l2 + 1);
            try {
                JSON.parse(c2);
                return c2;
            } catch { }
        }
    }
    return fallback;
}

/**
 * Parse JSON safely and return a typed fallback on any failure.
 * Accepts either a string (stdout) or an already-parsed object.
 */
export function safeParse<T = any>(raw: unknown, fallback: T): T {
    // If it’s already an object/array, just return it.
    if (raw !== null && typeof raw === "object") {
        return raw as T;
    }
    const cleaned = sanitizeRawJson(
        typeof raw === "string" ? raw : String(raw ?? ""),
        JSON.stringify(fallback)
    );
    try {
        return JSON.parse(cleaned) as T;
    } catch {
        return fallback;
    }
}


/**
 * Accepts stdout that could be:
 *   - a JSON array
 *   - an object like { error: string }
 *   - an envelope { ok: true, data: [...] } or { ok: false, error: ... } (future-proof)
 * Returns a uniform { data: T[], error?: string }.
 */
export function unpackArray<T = any>(
    raw: unknown,
    defaultValue: T[] = []
): { data: T[]; error?: string } {
    // safeParse handles strings or already-parsed objects
    const val = safeParse<any>(typeof raw === "string" ? raw : (raw ?? ""), defaultValue);

    if (Array.isArray(val)) return { data: val };

    if (val && typeof val === "object") {
        if (Array.isArray((val as any).data)) {
            return { data: (val as any).data, error: typeof (val as any).error === "string" ? (val as any).error : undefined };
        }
        if (typeof (val as any).error === "string") {
            return { data: defaultValue, error: (val as any).error };
        }
    }
    return { data: defaultValue };
}
