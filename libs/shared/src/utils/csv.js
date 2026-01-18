export const toCsv = (rows, header) => {
    const escape = (v) => {
        if (v === null || v === undefined)
            return '';
        const s = String(v);
        const needsQuote = /[",\r\n]/.test(s);
        const doubled = s.replace(/"/g, '""');
        return needsQuote ? `"${doubled}"` : doubled;
    };
    const lines = [];
    lines.push(header.map((h) => escape(h)).join(','));
    for (const row of rows) {
        lines.push(header.map((h) => escape(row[h])).join(','));
    }
    return lines.join('\r\n') + '\r\n';
};
