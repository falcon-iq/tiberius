# shared-util

Shared utility library containing common helper functions.

## Structure

- `src/lib/` - Library source code
- `src/lib/types/` - Type definitions (if needed)
- `src/lib/tests/` - Test files (_.spec.ts, _.test.ts)

## Features

- CSV utilities for converting data to CSV format

## Usage

```typescript
import { toCsv } from "@libs/shared/utils";

const data = [
  { name: "John", age: 30 },
  { name: "Jane", age: 25 },
];

const csv = toCsv(data, ["name", "age"]);
```
