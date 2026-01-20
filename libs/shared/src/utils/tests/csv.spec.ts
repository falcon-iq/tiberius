/**
 * @jest-environment node
 */

import { toCsv } from '../csv';

describe('toCsv', () => {
    it('should convert data to CSV format', () => {
        const data = [
            { name: 'John', age: 30 },
            { name: 'Jane', age: 25 },
        ];

        const result = toCsv(data, ['name', 'age']);

        expect(result).toContain('name,age');
        expect(result).toContain('John,30');
        expect(result).toContain('Jane,25');
    });

    it('should handle strings with quotes and commas', () => {
        const data = [{ name: 'Smith, John "Jr."', value: 'test' }];

        const result = toCsv(data, ['name', 'value']);

        expect(result).toContain('"Smith, John ""Jr."""');
    });

    it('should handle null and undefined values', () => {
        const data = [{ name: null, value: undefined }];

        const result = toCsv(data as Array<Record<string, unknown>>, ['name', 'value']);

        expect(result).toContain('name,value');
        expect(result).toContain(',\r\n'); // empty values for both columns
    });
});
