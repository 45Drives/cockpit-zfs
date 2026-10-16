/**
 * Pulls out the most likely JSON object/array from a mixed stdout string.
 * Returns a JSON string (so existing JSON.parse call sites can stay unchanged).
 */
export function sanitizeRawJson(raw: string, fallback = "[]"): string {
    const text = (raw ?? "").trim();
    if (!text) return fallback;
    try {
        JSON.parse(text);
        return text;
    } catch { }

    let result = fallback;
    let start = -1;
    const closing: string[] = [];
    let quoted = false;
    let escaped = false;
    for (let index = 0; index < text.length; index++) {
        const character = text[index];
        if (start === -1) {
            if (character !== '{' && character !== '[') continue;
            start = index;
        }
        if (quoted) {
            if (escaped) escaped = false;
            else if (character === '\\') escaped = true;
            else if (character === '"') quoted = false;
            continue;
        }
        if (character === '"') quoted = true;
        else if (character === '{') closing.push('}');
        else if (character === '[') closing.push(']');
        else if (character === '}' || character === ']') {
            if (closing.pop() !== character) {
                closing.length = 0;
                start = -1;
                continue;
            }
            if (closing.length === 0) {
                const candidate = text.slice(start, index + 1);
                try {
                    JSON.parse(candidate);
                    result = candidate;
                } catch { }
                start = -1;
            }
        }
    }
    return result;
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
    const val = safeParse<any>(raw, null);

    if (Array.isArray(val)) return { data: val };

    if (val && typeof val === "object") {
        if (val.ok === false) return { data: defaultValue, error: typeof val.error === 'string' ? val.error : 'Discovery failed.' };
        if (Array.isArray((val as any).data)) {
            return { data: (val as any).data, error: typeof (val as any).error === "string" ? (val as any).error : undefined };
        }
        if (typeof (val as any).error === "string") {
            return { data: defaultValue, error: (val as any).error };
        }
    }
    return { data: defaultValue, error: 'Invalid discovery response: expected an array or data envelope.' };
}
