import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useEffect, useId, useRef } from 'react';
import { createPortal } from 'react-dom';
import { X } from 'lucide-react';
const SIZE_CLASS = {
    sm: 'max-w-sm',
    md: 'max-w-md',
    lg: 'max-w-lg',
    xl: 'max-w-xl',
};
export function Modal({ isOpen, onClose, title, children, size = "md", closeOnBackdrop = true, closeOnEscape = true, showCloseButton = true, initialFocusId, }) {
    const titleId = useId();
    const panelRef = useRef(null);
    const lastActiveElementRef = useRef(null);
    // NEW: ensure we only apply initial focus once per open
    const didSetInitialFocusRef = useRef(false);
    useEffect(() => {
        if (!isOpen)
            return;
        // Reset per-open flag
        didSetInitialFocusRef.current = false;
        // Save focus so we can restore it on close
        lastActiveElementRef.current = document.activeElement;
        const onKeyDown = (e) => {
            if (closeOnEscape && e.key === 'Escape') {
                e.preventDefault();
                onClose();
            }
            if (e.key === 'Tab' && panelRef.current) {
                const focusableElements = panelRef.current.querySelectorAll('button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])');
                const firstElement = focusableElements[0];
                const lastElement = focusableElements[focusableElements.length - 1];
                if (!firstElement || !lastElement)
                    return;
                if (e.shiftKey && document.activeElement === firstElement) {
                    e.preventDefault();
                    lastElement.focus();
                }
                else if (!e.shiftKey && document.activeElement === lastElement) {
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
            if (!isOpen)
                return;
            if (didSetInitialFocusRef.current)
                return;
            didSetInitialFocusRef.current = true;
            const el = (initialFocusId ? document.getElementById(initialFocusId) : null) ??
                panelRef.current;
            el?.focus();
        });
        return () => {
            document.removeEventListener('keydown', onKeyDown);
            document.body.style.overflow = prevOverflow;
            lastActiveElementRef.current?.focus();
        };
    }, [isOpen, onClose, closeOnEscape, initialFocusId]);
    if (!isOpen)
        return null;
    const modalContent = (_jsx("div", { className: "fixed inset-0 z-50 flex items-center justify-center bg-black/50 dark:bg-white/10 backdrop-blur-sm p-4", onMouseDown: (e) => {
            if (!closeOnBackdrop)
                return;
            if (e.target === e.currentTarget)
                onClose();
        }, role: "dialog", "aria-modal": "true", "aria-labelledby": title ? titleId : undefined, children: _jsxs("div", { ref: panelRef, tabIndex: -1, className: [
                'w-full',
                SIZE_CLASS[size],
                'rounded-lg bg-card p-6 shadow-lg outline-none',
            ].filter(Boolean).join(' '), onMouseDown: (e) => e.stopPropagation(), children: [_jsxs("div", { className: "mb-6 flex items-center justify-between", children: [title ? (_jsx("h2", { id: titleId, className: "text-xl font-semibold text-foreground", children: title })) : (_jsx("span", {})), showCloseButton && (_jsx("button", { onClick: onClose, className: "rounded-lg p-1 text-muted-foreground transition-colors hover:bg-accent hover:text-foreground", "aria-label": "Close", type: "button", children: _jsx(X, { className: "h-5 w-5" }) }))] }), children] }) }));
    // Ensure document.body exists before creating portal
    if (typeof document !== 'undefined' && document.body) {
        return createPortal(modalContent, document.body);
    }
    // Fallback to regular rendering if document.body not available
    return modalContent;
}
