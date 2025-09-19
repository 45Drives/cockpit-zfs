const td = typeof TextDecoder !== "undefined" ? new TextDecoder("utf-8") : null;

// Accepts string | Uint8Array | null/undefined and always returns a string
export function toText(data?: string | Uint8Array | null): string {
    if (data == null) return "";
    if (typeof data === "string") return data;
    if (td) return td.decode(data);
    // Node fallback (rarely needed in your stack, but safe)
    // @ts-ignore
    return Buffer.from(data).toString("utf-8");
}