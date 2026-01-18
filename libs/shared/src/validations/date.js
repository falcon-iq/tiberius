/**
 * Validates a date string in ISO format (YYYY-MM-DD).
 * @param s - The date string to validate
 * @returns The validated ISO date string
 * @throws Error if the date string is invalid
 */
export const validateIsoDate = (s) => {
    if (!/^\d{4}-\d{2}-\d{2}$/.test(s)) {
        throw new Error(`Invalid date '${s}'. Expected YYYY-MM-DD.`);
    }
    const d = new Date(`${s}T00:00:00Z`);
    if (Number.isNaN(d.getTime()))
        throw new Error(`Invalid date '${s}'.`);
    return s;
};
