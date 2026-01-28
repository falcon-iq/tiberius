/**
 * Format ISO date string to dd-MM-yyyy
 * @param isoDate - ISO 8601 date string
 * @returns Formatted date string (dd-MM-yyyy)
 */
export function formatDate(isoDate: string): string {
  const date = new Date(isoDate);
  const day = String(date.getDate()).padStart(2, '0');
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const year = date.getFullYear();
  return `${day}-${month}-${year}`;
}

/**
 * Get current timestamp in ISO format
 */
export function getCurrentTimestamp(): string {
  return new Date().toISOString();
}
