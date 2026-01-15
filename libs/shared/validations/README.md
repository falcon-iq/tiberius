# @tiberius/shared-validations

Shared validation utilities for the Tiberius monorepo.

## Installation

This library is part of the Tiberius monorepo. Import it using:

```typescript
import { validateIsoDate, type IsoDate } from '@libs/shared/validations';
```

## API

### `validateIsoDate(s: string): IsoDate`

Validates a date string in ISO format (YYYY-MM-DD).

**Parameters:**
- `s` - The date string to validate

**Returns:**
- The validated ISO date string

**Throws:**
- Error if the date string is invalid

**Example:**

```typescript
import { validateIsoDate } from '@libs/shared/validation';

const date = validateIsoDate('2024-01-15'); // OK
validateIsoDate('invalid'); // Throws Error: Invalid date 'invalid'. Expected YYYY-MM-DD.
```

### `IsoDate`

Type alias for a validated ISO date string (YYYY-MM-DD format).

```typescript
type IsoDate = string;
```
