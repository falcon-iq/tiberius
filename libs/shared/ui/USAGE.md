# Usage Example

To use the shared modal component in your Electron app, you can import it like this:

```tsx
// In any component file, e.g., apps/falcon-iq-electron-app/src/renderer/components/example.tsx
import { useState } from 'react';
import { Modal } from '@libs/shared/ui';

export function ExampleComponent() {
  const [isModalOpen, setIsModalOpen] = useState(false);

  return (
    <div>
      <button onClick={() => setIsModalOpen(true)}>
        Open Modal
      </button>

      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Example Modal"
      >
        <p>This is the modal content!</p>
        <button onClick={() => setIsModalOpen(false)}>
          Close
        </button>
      </Modal>
    </div>
  );
}
```

## Adding Styles

The modal component uses the following CSS classes that you can style:
- `.modal-overlay` - The backdrop overlay
- `.modal-content` - The modal container
- `.modal-title` - The modal title
- `.modal-close` - The close button
- `.modal-body` - The modal content wrapper

You can add these styles to your `globals.css` or create a separate modal stylesheet.
