# Import Path Configuration

The TypeScript path alias has been configured for the shared UI library.

## Usage

You can now import components from the shared UI library using:

```typescript
import { Modal } from '@libs/shared/ui';
```

## Example

```tsx
import { useState } from 'react';
import { Modal } from '@libs/shared/ui';

export function MyComponent() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div>
      <button onClick={() => setIsOpen(true)}>
        Open Modal
      </button>

      <Modal
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        title="Example Modal"
        size="md"
        closeOnBackdrop={true}
        closeOnEscape={true}
      >
        <p className="text-foreground">
          This is the modal content!
        </p>
        <div className="mt-4 flex justify-end gap-2">
          <button 
            onClick={() => setIsOpen(false)}
            className="rounded-lg bg-primary px-4 py-2 text-primary-foreground"
          >
            Close
          </button>
        </div>
      </Modal>
    </div>
  );
}
```

## Available Exports

From `@libs/shared/ui`:
- `Modal` - The modal component
- `ModalProps` - TypeScript interface for Modal props
- `ModalSize` - Type for modal sizes ('sm' | 'md' | 'lg' | 'xl')

## Configuration

The path alias is configured in:
- `tsconfig.base.json` - TypeScript path mapping
- `vite.renderer.config.mts` - Vite uses `vite-tsconfig-paths` plugin to automatically resolve the paths
