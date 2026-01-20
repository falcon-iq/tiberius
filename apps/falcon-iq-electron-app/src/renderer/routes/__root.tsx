import { createRootRoute, Outlet } from '@tanstack/react-router';
import { TanStackRouterDevtools } from '@tanstack/router-devtools';
import NavigationSidebar from '@components/navigation-side-bar';
import MainWorkArea from '@components/main-work-area';
import AgentSidebar from '@components/agent-side-bar';
import { useTheme } from '@libs/shared/hooks/use-theme';

export const Route = createRootRoute({
  component: RootLayout,
});

function RootLayout() {
  const { theme, toggleTheme } = useTheme();

  return (
    <>
      <div className="flex h-screen w-full overflow-hidden bg-background">
        {/* Left Sidebar - Navigation */}
        <NavigationSidebar theme={theme} onToggleTheme={toggleTheme} />

        {/* Main Work Area - Center */}
        <MainWorkArea>
          <Outlet />
        </MainWorkArea>

        {/* Right Sidebar - AI Agent */}
        <AgentSidebar />
      </div>
      {import.meta.env.DEV ? <TanStackRouterDevtools /> : null}
    </>
  );
}

