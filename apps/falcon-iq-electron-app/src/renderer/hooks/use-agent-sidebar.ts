import { useState, useEffect, useCallback } from 'react';

const MIN_WIDTH = 256;  // 16rem (w-64)
const MAX_WIDTH = 640;  // 40rem (w-160)
const DEFAULT_WIDTH = 320;  // 20rem (w-80)
const COLLAPSED_WIDTH = 48;  // 3rem - width when collapsed (shows toggle button)
const STORAGE_KEY = 'agent-sidebar-state';

interface AgentSidebarState {
  isCollapsed: boolean;
  width: number;
}

export function useAgentSidebar() {
  // Initialize from localStorage with validation
  const [state, setState] = useState<AgentSidebarState>(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        try {
          const parsed = JSON.parse(saved);
          if (typeof parsed.isCollapsed === 'boolean' &&
              typeof parsed.width === 'number') {
            return {
              isCollapsed: parsed.isCollapsed,
              width: Math.max(MIN_WIDTH, Math.min(MAX_WIDTH, parsed.width))
            };
          }
        } catch {
          // Fall through to default
        }
      }
    }
    return { isCollapsed: false, width: DEFAULT_WIDTH };
  });

  const [isResizing, setIsResizing] = useState(false);

  // Persist to localStorage
  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  }, [state]);

  const toggleCollapse = useCallback(() => {
    setState(prev => ({ ...prev, isCollapsed: !prev.isCollapsed }));
  }, []);

  const setWidth = useCallback((width: number) => {
    const clampedWidth = Math.max(MIN_WIDTH, Math.min(MAX_WIDTH, width));
    setState(prev => ({ ...prev, width: clampedWidth }));
  }, []);

  const startResize = useCallback(() => {
    setIsResizing(true);
  }, []);

  const endResize = useCallback(() => {
    setIsResizing(false);
  }, []);

  return {
    isCollapsed: state.isCollapsed,
    width: state.width,
    isResizing,
    toggleCollapse,
    setWidth,
    startResize,
    endResize,
    minWidth: MIN_WIDTH,
    maxWidth: MAX_WIDTH,
    collapsedWidth: COLLAPSED_WIDTH,
  };
}
