import { validateIsoDate } from '../date';
describe('validateIsoDate', () => {
    describe('valid dates', () => {
        it('should accept a valid ISO date in YYYY-MM-DD format', () => {
            const result = validateIsoDate('2024-01-15');
            expect(result).toBe('2024-01-15');
        });
        it('should accept leap year date', () => {
            const result = validateIsoDate('2024-02-29');
            expect(result).toBe('2024-02-29');
        });
        it('should accept date at year boundaries', () => {
            expect(validateIsoDate('2024-01-01')).toBe('2024-01-01');
            expect(validateIsoDate('2024-12-31')).toBe('2024-12-31');
        });
        it('should accept historical dates', () => {
            const result = validateIsoDate('1900-01-01');
            expect(result).toBe('1900-01-01');
        });
        it('should accept future dates', () => {
            const result = validateIsoDate('2099-12-31');
            expect(result).toBe('2099-12-31');
        });
        it('should return the same string that was passed in', () => {
            const input = '2024-06-15';
            const result = validateIsoDate(input);
            expect(result).toBe(input);
            expect(typeof result).toBe('string');
        });
    });
    describe('invalid format', () => {
        it('should throw error for date with wrong separator', () => {
            expect(() => validateIsoDate('2024/01/15')).toThrow("Invalid date '2024/01/15'. Expected YYYY-MM-DD.");
        });
        it('should throw error for date without separators', () => {
            expect(() => validateIsoDate('20240115')).toThrow("Invalid date '20240115'. Expected YYYY-MM-DD.");
        });
        it('should throw error for date with time component', () => {
            expect(() => validateIsoDate('2024-01-15T12:00:00')).toThrow("Invalid date '2024-01-15T12:00:00'. Expected YYYY-MM-DD.");
        });
        it('should throw error for short year format', () => {
            expect(() => validateIsoDate('24-01-15')).toThrow("Invalid date '24-01-15'. Expected YYYY-MM-DD.");
        });
        it('should throw error for single digit month', () => {
            expect(() => validateIsoDate('2024-1-15')).toThrow("Invalid date '2024-1-15'. Expected YYYY-MM-DD.");
        });
        it('should throw error for single digit day', () => {
            expect(() => validateIsoDate('2024-01-5')).toThrow("Invalid date '2024-01-5'. Expected YYYY-MM-DD.");
        });
        it('should throw error for reversed date format (DD-MM-YYYY)', () => {
            expect(() => validateIsoDate('15-01-2024')).toThrow("Invalid date '15-01-2024'. Expected YYYY-MM-DD.");
        });
        it('should throw error for US format (MM-DD-YYYY)', () => {
            expect(() => validateIsoDate('01-15-2024')).toThrow("Invalid date '01-15-2024'. Expected YYYY-MM-DD.");
        });
    });
    describe('invalid date values', () => {
        it('should throw error for invalid month', () => {
            expect(() => validateIsoDate('2024-13-01')).toThrow("Invalid date '2024-13-01'.");
        });
        it('should throw error for zero month', () => {
            expect(() => validateIsoDate('2024-00-15')).toThrow("Invalid date '2024-00-15'.");
        });
        it('should throw error for invalid day', () => {
            expect(() => validateIsoDate('2024-01-32')).toThrow("Invalid date '2024-01-32'.");
        });
        it('should throw error for zero day', () => {
            expect(() => validateIsoDate('2024-01-00')).toThrow("Invalid date '2024-01-00'.");
        });
        // Note: JavaScript Date constructor is lenient and adjusts overflow dates
        // e.g., 2024-02-30 becomes 2024-03-01. The current implementation only
        // checks format and if the date is parseable, not if days overflow.
        // These tests document the current behavior.
        it('should accept February 30th (JS Date adjusts to March)', () => {
            // Current behavior: does not throw (Date constructor adjusts)
            expect(() => validateIsoDate('2024-02-30')).not.toThrow();
        });
        it('should accept February 29th in non-leap year (JS Date adjusts)', () => {
            // Current behavior: does not throw (Date constructor adjusts to March 1)
            expect(() => validateIsoDate('2023-02-29')).not.toThrow();
        });
        it('should accept April 31st (JS Date adjusts to May 1)', () => {
            // Current behavior: does not throw (Date constructor adjusts)
            expect(() => validateIsoDate('2024-04-31')).not.toThrow();
        });
    });
    describe('edge cases', () => {
        it('should throw error for empty string', () => {
            expect(() => validateIsoDate('')).toThrow("Invalid date ''. Expected YYYY-MM-DD.");
        });
        it('should throw error for whitespace', () => {
            expect(() => validateIsoDate('   ')).toThrow("Invalid date '   '. Expected YYYY-MM-DD.");
        });
        it('should throw error for null-like strings', () => {
            expect(() => validateIsoDate('null')).toThrow("Invalid date 'null'. Expected YYYY-MM-DD.");
        });
        it('should throw error for undefined-like strings', () => {
            expect(() => validateIsoDate('undefined')).toThrow("Invalid date 'undefined'. Expected YYYY-MM-DD.");
        });
        it('should throw error for date with extra spaces', () => {
            expect(() => validateIsoDate(' 2024-01-15 ')).toThrow("Invalid date ' 2024-01-15 '. Expected YYYY-MM-DD.");
        });
        it('should throw error for date with extra dashes', () => {
            expect(() => validateIsoDate('2024-01-15-')).toThrow("Invalid date '2024-01-15-'. Expected YYYY-MM-DD.");
        });
    });
    describe('type compatibility', () => {
        it('should return IsoDate type', () => {
            const result = validateIsoDate('2024-01-15');
            expect(typeof result).toBe('string');
        });
        it('should be assignable to string', () => {
            const result = validateIsoDate('2024-01-15');
            const str = result;
            expect(str).toBe('2024-01-15');
        });
    });
});
