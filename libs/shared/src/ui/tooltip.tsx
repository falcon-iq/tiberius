import {
  ReactNode,
  useState,
  useRef,
  useEffect,
  useLayoutEffect,
  useId,
} from 'react';
import { createPortal } from 'react-dom';

export interface TooltipProps {
  children: ReactNode;
  content: string | ReactNode;
  position?: 'top' | 'right' | 'bottom' | 'left';
  delay?: number;
  offset?: number;
  disabled?: boolean;
}

export function Tooltip({
  children,
  content,
  position = 'right',
  delay = 300,
  offset = 8,
  disabled = false,
}: TooltipProps) {
  const [isVisible, setIsVisible] = useState(false);
  const [coords, setCoords] = useState({ top: 0, left: 0 });
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  const triggerRef = useRef<HTMLDivElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);
  const tooltipId = useId();

  const handleMouseEnter = () => {
    if (disabled) return;
    timeoutRef.current = setTimeout(() => {
      setIsVisible(true);
    }, delay);
  };

  const handleMouseLeave = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
    setIsVisible(false);
  };

  const handleFocus = () => {
    if (disabled) return;
    setIsVisible(true);
  };

  const handleBlur = () => {
    setIsVisible(false);
  };

  useLayoutEffect(() => {
    if (!isVisible || !triggerRef.current || !tooltipRef.current) return;

    const triggerRect = triggerRef.current.getBoundingClientRect();
    const tooltipRect = tooltipRef.current.getBoundingClientRect();

    let top = 0;
    let left = 0;

    switch (position) {
      case 'right':
        top =
          triggerRect.top +
          triggerRect.height / 2 -
          tooltipRect.height / 2;
        left = triggerRect.right + offset;
        break;
      case 'left':
        top =
          triggerRect.top +
          triggerRect.height / 2 -
          tooltipRect.height / 2;
        left = triggerRect.left - tooltipRect.width - offset;
        break;
      case 'top':
        top = triggerRect.top - tooltipRect.height - offset;
        left =
          triggerRect.left +
          triggerRect.width / 2 -
          tooltipRect.width / 2;
        break;
      case 'bottom':
        top = triggerRect.bottom + offset;
        left =
          triggerRect.left +
          triggerRect.width / 2 -
          tooltipRect.width / 2;
        break;
    }

    setCoords({ top, left });
  }, [isVisible, position, offset]);

  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  return (
    <>
      <div
        ref={triggerRef}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        onFocus={handleFocus}
        onBlur={handleBlur}
        aria-describedby={isVisible ? tooltipId : undefined}
      >
        {children}
      </div>

      {typeof document !== 'undefined' &&
        document.body &&
        createPortal(
          <div
            ref={tooltipRef}
            id={tooltipId}
            role="tooltip"
            className={`
              fixed z-50 px-3 py-1.5 text-sm rounded-md
              bg-popover text-popover-foreground
              border border-border shadow-lg
              transition-opacity duration-150
              ${isVisible ? 'opacity-100' : 'opacity-0 pointer-events-none'}
            `}
            style={{
              top: `${coords.top}px`,
              left: `${coords.left}px`,
            }}
          >
            {content}
          </div>,
          document.body
        )}
    </>
  );
}
