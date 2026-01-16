# @libs/shared/hooks

Reusable React hooks for common patterns across Tiberius applications.

## Available Hooks

### `useAsyncValidation`

A custom hook for handling async validation with built-in guards against:
- **Re-entrancy**: Prevents multiple simultaneous validations
- **Value deduplication**: Prevents validating the same value repeatedly
- **Proper cleanup**: Cleans up timers on unmount
- **Error handling**: Gracefully handles exceptions with fallback messages

#### Basic Usage

```typescript
import { useAsyncValidation } from '@libs/shared/hooks';
import { validateGitHubToken } from '@libs/integrations/github/auth';

function MyComponent() {
  const { validate, isValidating, validationError, isValid } = useAsyncValidation({
    validator: validateGitHubToken,
    extractErrorMessage: (result) => result.error || "Invalid token",
    fallbackErrorMessage: "Failed to validate. Please check your connection."
  });

  return (
    <div>
      <input
        type="password"
        onBlur={(e) => validate(e.target.value)}
        className={validationError ? "border-red-500" : "border-gray-300"}
      />
      
      {isValidating && <Spinner />}
      
      {validationError && (
        <p className="text-red-500">{validationError}</p>
      )}
      
      <button disabled={!isValid || isValidating}>
        Submit
      </button>
    </div>
  );
}
```

#### API Reference

##### Options

```typescript
interface UseAsyncValidationOptions<T> {
  // The async validator function
  validator: (value: string) => Promise<T>;
  
  // Extracts error message from validation result
  extractErrorMessage?: (result: T) => string | undefined;
  
  // Fallback error message for exceptions
  fallbackErrorMessage?: string;
  
  // Called when validation succeeds
  onSuccess?: (result: T) => void;
  
  // Called when validation fails
  onError?: (error: string) => void;
}
```

##### Return Value

```typescript
interface UseAsyncValidationReturn {
  // Trigger validation
  validate: (value: string) => Promise<void>;
  
  // True while validation is in progress
  isValidating: boolean;
  
  // Error message if validation failed
  validationError: string;
  
  // True if last validation succeeded
  isValid: boolean;
  
  // Reset all validation state
  reset: () => void;
}
```

#### Advanced Examples

##### With Custom Error Extraction

```typescript
interface CustomValidationResult {
  valid: boolean;
  error?: string;
  details?: string;
}

const { validate, validationError } = useAsyncValidation({
  validator: myCustomValidator,
  extractErrorMessage: (result) => result.details || result.error || "Unknown error"
});
```

##### With Callbacks

```typescript
const { validate } = useAsyncValidation({
  validator: validateEmail,
  onSuccess: (result) => {
    console.log('Email validated successfully:', result);
    // Maybe save to state or trigger next step
  },
  onError: (error) => {
    console.error('Email validation failed:', error);
    // Maybe log to analytics
  }
});
```

##### With Reset

```typescript
function FormComponent() {
  const validation = useAsyncValidation({
    validator: validateField
  });

  const handleCancel = () => {
    validation.reset(); // Clear validation state
    // Clear form or navigate away
  };

  return (
    <>
      <input onBlur={(e) => validation.validate(e.target.value)} />
      <button onClick={handleCancel}>Cancel</button>
    </>
  );
}
```

#### Behavior Details

1. **Empty Values**: Validating an empty string (or whitespace-only) resets validation state
2. **Trimming**: Input values are automatically trimmed before validation
3. **Deduplication**: The same value won't be validated twice in a row (unless reset)
4. **Re-entrancy**: If validation is in progress, new validation attempts are ignored
5. **Error Recovery**: After an exception, the deduplication is reset so the user can retry

#### Type Safety

The hook is fully typed and will infer types from your validator:

```typescript
interface GitHubTokenResult {
  valid: boolean;
  error?: string;
  username?: string;
}

const { validate } = useAsyncValidation({
  validator: async (token: string): Promise<GitHubTokenResult> => {
    // ... implementation
  },
  extractErrorMessage: (result) => {
    // TypeScript knows result is GitHubTokenResult
    return result.error;
  },
  onSuccess: (result) => {
    // TypeScript knows result is GitHubTokenResult
    console.log('Validated user:', result.username);
  }
});
```

## Development

### Building

```bash
npx nx build shared-hooks
```

### Testing

```bash
npx nx test shared-hooks
```

### Linting

```bash
npx nx lint shared-hooks
```

## Related Libraries

- `@libs/shared/ui` - Shared UI components
- `@libs/shared/utils` - Pure utility functions
- `@libs/shared/validations` - Validation utilities
