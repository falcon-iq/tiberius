# Shared UI Library

This library contains shared UI components for the Tiberius project.

## Components

### Modal

A reusable modal dialog component.

#### Usage

```tsx
import { Modal } from '@tiberius/shared-ui';

function MyComponent() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      <button onClick={() => setIsOpen(true)}>Open Modal</button>
      <Modal
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        title="My Modal"
      >
        <p>Modal content goes here</p>
      </Modal>
    </>
  );
}
```

#### Props

- `isOpen`: boolean - Controls modal visibility
- `onClose`: () => void - Callback when modal should close
- `title`: string (optional) - Modal title
- `children`: React.ReactNode - Modal content
