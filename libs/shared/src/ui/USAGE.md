# Usage Example

To use the shared modal component in your Electron app, you can import it like this:

```tsx
// In any component file, e.g., apps/falcon-iq-electron-app/src/renderer/components/example.tsx
import { useState } from "react";
import { Modal } from "@libs/shared/ui";

export function ExampleComponent() {
  const [isModalOpen, setIsModalOpen] = useState(false);

  return (
    <div>
      <button onClick={() => setIsModalOpen(true)}>Open Modal</button>

      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Example Modal"
        size="md"
      >
        <p>This is the modal content!</p>
        <button onClick={() => setIsModalOpen(false)}>Close</button>
      </Modal>
    </div>
  );
}
```

## Modal Props

- **`isOpen`** (boolean, required) - Controls whether the modal is visible
- **`onClose`** (function, required) - Callback when modal should close
- **`title`** (string, optional) - Modal title text
- **`size`** ('sm' | 'md' | 'lg' | 'xl', optional) - Modal width (default: 'md')
- **`closeOnBackdrop`** (boolean, optional) - Close when clicking backdrop (default: true)
- **`closeOnEscape`** (boolean, optional) - Close when pressing Escape (default: true)
- **`initialFocusId`** (string, optional) - ID of element to focus when modal opens

## Styling

The modal is fully styled using Tailwind CSS and respects your app's theme system (light/dark mode, custom colors, etc.). It uses semantic color tokens like:

- `bg-card` / `text-foreground` - Adapts to your theme
- `bg-black/50 dark:bg-white/10` - Backdrop (semi-transparent)
- `backdrop-blur-sm` - Blur effect on backdrop

**Customization:** Colors automatically adapt based on your `globals.css` theme configuration. No additional CSS needed!

## Features

- ✅ **Portal rendering** - Renders to `document.body` to escape parent constraints
- ✅ **Focus trap** - Keyboard navigation stays within modal (excludes disabled elements)
- ✅ **Accessibility** - WCAG compliant focus management, respects disabled states
- ✅ **Dark mode support** - Automatically adapts to light/dark themes
- ✅ **Backdrop blur** - Modern glass-morphism effect
- ✅ **Escape key** - Press ESC to close
- ✅ **Click outside** - Click backdrop to close
- ✅ **Focus management** - Auto-focus and focus restoration
