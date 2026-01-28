import { createRootRoute, Outlet } from '@tanstack/react-router';
import { TanStackRouterDevtools } from '@tanstack/router-devtools';
import NavigationSidebar from '@components/navigation-side-bar';
import MainWorkArea from '@components/main-work-area';
import AgentSidebar from '@components/agent-side-bar';
import { useTheme } from '@libs/shared/hooks/use-theme';
import { useAgentSidebar } from '@hooks/use-agent-sidebar';

export const Route = createRootRoute({
  component: RootLayout,
});

function RootLayout() {
  const { theme, toggleTheme } = useTheme();
  const agentSidebar = useAgentSidebar();

  return (
    <>
      <div
        className={`flex h-screen w-full overflow-hidden bg-background ${
          agentSidebar.isResizing ? 'select-none' : ''
        }`}
      >
        {/* Left Sidebar - Navigation */}
        <NavigationSidebar theme={theme} onToggleTheme={toggleTheme} />

        {/* Main Work Area - Center */}
        <MainWorkArea>
          <Outlet />
        </MainWorkArea>

        {/* Right Sidebar - AI Agent */}
        <AgentSidebar
          isCollapsed={agentSidebar.isCollapsed}
          width={agentSidebar.width}
          collapsedWidth={agentSidebar.collapsedWidth}
          isResizing={agentSidebar.isResizing}
          onToggleCollapse={agentSidebar.toggleCollapse}
          onWidthChange={agentSidebar.setWidth}
          onResizeStart={agentSidebar.startResize}
          onResizeEnd={agentSidebar.endResize}
        />
      </div>
      {import.meta.env.DEV ? <TanStackRouterDevtools /> : null}
    </>
  );
}

