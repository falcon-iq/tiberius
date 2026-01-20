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
  initialFocusId,
}: ModalProps) {
  const titleId = useId();
  const panelRef = useRef<HTMLDivElement | null>(null);
  const lastActiveElementRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (!isOpen) return;

    // Save focus so we can restore it on close
    lastActiveElementRef.current = document.activeElement as HTMLElement | null;

    const onKeyDown = (e: KeyboardEvent) => {
      if (closeOnEscape && e.key === 'Escape') {
        e.preventDefault();
        onClose();
      }

      // Focus trap: Tab key handling
      if (e.key === 'Tab' && panelRef.current) {
        const focusableElements = panelRef.current.querySelectorAll<HTMLElement>(
          'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
        );
        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];

        if (e.shiftKey && document.activeElement === firstElement) {
          e.preventDefault();
          lastElement?.focus();
        } else if (!e.shiftKey && document.activeElement === lastElement) {
          e.preventDefault();
          firstElement?.focus();
        }
      }
    };

    document.addEventListener('keydown', onKeyDown);

    // Lock background scroll
    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';

    // Focus management: focus initial target, else focus panel
    queueMicrotask(() => {
      const el =
        (initialFocusId ? document.getElementById(initialFocusId) : null) ??
        panelRef.current;
      el?.focus();
    });

    return () => {
      document.removeEventListener('keydown', onKeyDown);
      document.body.style.overflow = prevOverflow;

      // Restore focus
      lastActiveElementRef.current?.focus();
    };
  }, [isOpen, onClose, closeOnEscape, initialFocusId]);

  if (!isOpen) return null;

  const modalContent = (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 dark:bg-white/10 backdrop-blur-sm p-4"
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
          'rounded-lg bg-card p-6 shadow-lg outline-none',
        ].filter(Boolean).join(' ')}
        onMouseDown={(e) => e.stopPropagation()}
      >
        <div className="mb-6 flex items-center justify-between">
          {title ? (
            <h2 id={titleId} className="text-xl font-semibold text-foreground">
              {title}
            </h2>
          ) : (
            <span />
          )}

          <button
            onClick={onClose}
            className="rounded-lg p-1 text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
            aria-label="Close"
            type="button"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {children}
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

