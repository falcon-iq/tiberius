import { useEffect, useId, useRef, type ReactNode } from 'react';
import { createPortal } from 'react-dom';
import { X } from 'lucide-react';

export type ModalSize = 'sm' | 'md' | 'lg' | 'xl';

const SIZE_CLASS: Record<ModalSize, string> = {
  sm: 'max-w-sm',
  md: 'max-w-md',
  lg: 'max-w-lg',
  xl: 'max-w-xl',
};

export interface ModalProps {
  isOpen: boolean;
  onClose: () => void;

  title?: string;
  children: ReactNode;

  size?: ModalSize;

  /** If true, clicking the backdrop closes the modal (default true). */
  closeOnBackdrop?: boolean;

  /** If true, pressing Escape closes the modal (default true). */
  closeOnEscape?: boolean;

  /** If true, shows the X close button in the top right (default true). */
  showCloseButton?: boolean;

  /** Optional: focus this element (by id) when modal opens */
  initialFocusId?: string;
}

export function Modal({
  isOpen,
  onClose,
  title,
  children,
  size = "md",
  closeOnBackdrop = true,
  closeOnEscape = true,
  showCloseButton = true,
  initialFocusId,
}: ModalProps) {
  const titleId = useId();
  const panelRef = useRef<HTMLDivElement | null>(null);
  const lastActiveElementRef = useRef<HTMLElement | null>(null);

  // NEW: ensure we only apply initial focus once per open
  const didSetInitialFocusRef = useRef(false);

  useEffect(() => {
    if (!isOpen) return;

    // Reset per-open flag
    didSetInitialFocusRef.current = false;

    // Save focus so we can restore it on close
    lastActiveElementRef.current = document.activeElement as HTMLElement | null;

    const onKeyDown = (e: KeyboardEvent) => {
      if (closeOnEscape && e.key === 'Escape') {
        e.preventDefault();
        onClose();
      }

      if (e.key === 'Tab' && panelRef.current) {
        const focusableElements = panelRef.current.querySelectorAll<HTMLElement>(
          'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
        );

        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];

        if (!firstElement || !lastElement) return;

        if (e.shiftKey && document.activeElement === firstElement) {
          e.preventDefault();
          lastElement.focus();
        } else if (!e.shiftKey && document.activeElement === lastElement) {
          e.preventDefault();
          firstElement.focus();
        }
      }
    };

    document.addEventListener('keydown', onKeyDown);

    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';

    // Focus initial target ONCE per open
    queueMicrotask(() => {
      if (!isOpen) return;
      if (didSetInitialFocusRef.current) return;

      didSetInitialFocusRef.current = true;

      const el =
        (initialFocusId ? document.getElementById(initialFocusId) : null) ??
        panelRef.current;

      el?.focus();
    });

    return () => {
      document.removeEventListener('keydown', onKeyDown);
      document.body.style.overflow = prevOverflow;
      lastActiveElementRef.current?.focus();
    };
  }, [isOpen, onClose, closeOnEscape, initialFocusId]);

  if (!isOpen) return null;

  const modalContent = (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center bg-black/50 dark:bg-white/10 backdrop-blur-sm p-4 overflow-y-auto"
      onMouseDown={(e) => {
        if (!closeOnBackdrop) return;
        if (e.target === e.currentTarget) onClose();
      }}
      role="dialog"
      aria-modal="true"
      aria-labelledby={title ? titleId : undefined}
    >
      <div
        ref={panelRef}
        tabIndex={-1}
        className={[
          'w-full',
          SIZE_CLASS[size],
          'my-8',
          'rounded-lg bg-card shadow-lg outline-none',
          'flex flex-col',
          'max-h-[calc(100vh-4rem)]',
        ].filter(Boolean).join(' ')}
        onMouseDown={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between px-6 pt-6 pb-4 flex-shrink-0">
          {title ? (
            <h2 id={titleId} className="text-xl font-semibold text-foreground">
              {title}
            </h2>
          ) : (
            <span />
          )}

          {showCloseButton && (
            <button
              onClick={onClose}
              className="rounded-lg p-1 text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
              aria-label="Close"
              type="button"
            >
              <X className="h-5 w-5" />
            </button>
          )}
        </div>

        <div className="px-6 pb-6 overflow-y-auto flex-1">
          {children}
        </div>
      </div>
    </div>
  );

  // Ensure document.body exists before creating portal
  if (typeof document !== 'undefined' && document.body) {
    return createPortal(modalContent, document.body);
  }
  
  // Fallback to regular rendering if document.body not available
  return modalContent;
}

