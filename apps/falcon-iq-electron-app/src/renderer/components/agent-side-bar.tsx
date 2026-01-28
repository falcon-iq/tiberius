import { Sparkles, ChevronLeft, ChevronRight } from "lucide-react"

interface AgentSidebarProps {
  isCollapsed: boolean;
  width: number;
  collapsedWidth: number;
  isResizing: boolean;
  onToggleCollapse: () => void;
  onWidthChange: (width: number) => void;
  onResizeStart: () => void;
  onResizeEnd: () => void;
}

const AgentSidebar = ({
  isCollapsed,
  width,
  collapsedWidth,
  isResizing,
  onToggleCollapse,
  onWidthChange,
  onResizeStart,
  onResizeEnd,
}: AgentSidebarProps) => {
  const handleMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    onResizeStart();

    const startX = e.clientX;
    const startWidth = width;

    const handleMouseMove = (moveEvent: MouseEvent) => {
      const deltaX = moveEvent.clientX - startX;
      const newWidth = startWidth - deltaX;  // Right sidebar, so subtract
      onWidthChange(newWidth);
    };

    const handleMouseUp = () => {
      onResizeEnd();
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
  };

  return (
    <aside
      className={`relative flex flex-col border-l border-sidebar-border bg-sidebar ${
        !isResizing ? 'transition-[width] duration-300 ease-in-out' : ''
      }`}
      style={{ width: isCollapsed ? `${collapsedWidth}px` : `${width}px` }}
    >
      {/* Drag Handle */}
      {!isCollapsed && (
        <div
          className="absolute left-0 top-0 h-full cursor-col-resize border-r border-sidebar-border hover:bg-primary/10 active:bg-primary/20"
          style={{ width: '4px', marginLeft: '-2px' }}
          onMouseDown={handleMouseDown}
        />
      )}

      {/* Header with toggle */}
      <div className="flex h-16 items-center gap-2 border-b border-sidebar-border px-4">
        <button
          onClick={onToggleCollapse}
          className="flex h-8 w-8 items-center justify-center rounded-lg hover:bg-muted"
          aria-label={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {isCollapsed ? <ChevronLeft className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
        </button>
        {!isCollapsed && (
          <>
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10">
              <Sparkles className="h-4 w-4 text-primary" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-foreground">AI Buddy</h2>
              <p className="text-xs text-muted-foreground">Your helpful assistant</p>
            </div>
          </>
        )}
      </div>

      {!isCollapsed && (
        <>
          {/* Feed Content */}
          <div className="flex-1 overflow-y-auto p-4">
            <div className="space-y-4">
              {/* Sample Feed Item */}
              <div className="rounded-lg border border-border bg-background p-4">
                <div className="mb-2 flex items-center gap-2">
                  <div className="h-2 w-2 rounded-full bg-primary" />
                  <span className="text-xs font-medium text-muted-foreground">Insight</span>
                </div>
                <p className="text-sm text-foreground">AI-powered insights and suggestions will appear here.</p>
              </div>

              <div className="rounded-lg border border-border bg-background p-4">
                <div className="mb-2 flex items-center gap-2">
                  <div className="h-2 w-2 rounded-full bg-accent" />
                  <span className="text-xs font-medium text-muted-foreground">Action</span>
                </div>
                <p className="text-sm text-foreground">Suggested actions and quick notes will be displayed here.</p>
              </div>
            </div>
          </div>

          {/* Input Area */}
          <div className="border-t border-sidebar-border p-4">
            <div className="flex items-center gap-2 rounded-lg border border-input bg-background px-3 py-2">
              <input
                type="text"
                placeholder="Ask your buddy..."
                className="flex-1 bg-transparent text-sm text-foreground outline-none placeholder:text-muted-foreground"
              />
              <Sparkles className="h-4 w-4 text-muted-foreground" />
            </div>
          </div>
        </>
      )}
    </aside>
  )
}

export default AgentSidebar;