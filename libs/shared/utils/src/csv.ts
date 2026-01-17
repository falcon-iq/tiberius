export const toCsv = <T extends Record<string, unknown>>(
    rows: T[],
    header: ReadonlyArray<Extract<keyof T, string>>
): string => {
    const escape = (v: unknown): string => {
        if (v === null || v === undefined) return '';
        const s = String(v);
        const needsQuote = /[",\r\n]/.test(s);
        const doubled = s.replace(/"/g, '""');
        return needsQuote ? `"${doubled}"` : doubled;
    };

    const lines: string[] = [];
    lines.push(header.map((h) => escape(h)).join(','));
    for (const row of rows) {
        lines.push(header.map((h) => escape(row[h])).join(','));
    }
    return lines.join('\r\n') + '\r\n';
};
