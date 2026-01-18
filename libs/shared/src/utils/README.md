# @tiberius/shared-utils

Shared utility library containing common helper functions for the Tiberius monorepo.

## Installation

This library is part of the Tiberius monorepo. Import it using:

```typescript
import { toCsv, getLogger } from '@libs/shared/utils';
```

## API

### CSV Utilities

#### `toCsv<T>(rows: T[], header: ReadonlyArray<Extract<keyof T, string>>): string`

Converts an array of objects to CSV format with proper escaping.

**Example:**

```typescript
import { toCsv } from '@libs/shared/utils';

const data = [
  { name: 'John', age: 30 },
  { name: 'Jane', age: 25 },
];

const csv = toCsv(data, ['name', 'age']);
// Output:
// name,age
// John,30
// Jane,25
```

### Logger Utilities

#### `getLogger(options): Logger`

Creates a configured logger instance with support for different log levels.

**Example:**

```typescript
import { getLogger } from '@libs/shared/utils';

const logger = getLogger({
  name: 'my-app',
  level: 'info',
  base: { service: 'api' }
});

logger.info({ userId: 123 }, 'User logged in');
logger.error({ error: err }, 'Failed to process request');
```

### Date Utilities

Provides helper functions for working with dates.

## Structure

- `src/lib/csv.ts` - CSV conversion utilities
- `src/lib/logger.ts` - Logging utilities
- `src/lib/date.ts` - Date helper functions
- `src/lib/tests/` - Test files
