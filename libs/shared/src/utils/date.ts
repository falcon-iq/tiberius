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

/**
 * Convert Date object or ISO string to YYYY-MM-DD format (for HTML5 date input)
 * @param date - Date object or ISO string
 * @returns Date string in YYYY-MM-DD format
 */
export function toDateInputValue(date: Date | string): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

/**
 * Convert YYYY-MM-DD date string to ISO timestamp
 * @param dateString - Date string in YYYY-MM-DD format
 * @returns ISO 8601 timestamp
 */
export function dateInputToISO(dateString: string): string {
  return new Date(dateString).toISOString();
}

/**
 * Get today's date in YYYY-MM-DD format (for HTML5 date input default value)
 * @returns Today's date in YYYY-MM-DD format
 */
export function getTodayDateInputValue(): string {
  return toDateInputValue(new Date());
}
