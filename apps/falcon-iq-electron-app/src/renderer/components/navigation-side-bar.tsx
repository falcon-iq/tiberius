import { Users, Goal, Settings, Sun, Moon } from "lucide-react"
import { Link } from "@tanstack/react-router"
import { Tooltip } from "@libs/shared/ui/tooltip"

interface NavigationSidebarProps {
  theme: "light" | "dark"
  onToggleTheme: () => void
}

const NavigationSidebar = ({ theme, onToggleTheme }: NavigationSidebarProps) => (
    <div className="flex w-16 flex-col items-center gap-4 border-r border-sidebar-border bg-sidebar py-6">
        {/* Logo */}
        <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-primary">
        <span className="text-lg font-bold text-primary-foreground">MB</span>
        </div>

        {/* Navigation Items */}
        <nav className="flex flex-1 flex-col gap-2">
        <Tooltip content="Dashboard" position="right">
          <Link
              to="/"
              className="group relative flex h-11 w-11 items-center justify-center rounded-lg text-sidebar-foreground/60 transition-colors hover:bg-sidebar-accent hover:text-sidebar-foreground"
              activeProps={{
                className: "group relative flex h-11 w-11 items-center justify-center rounded-lg bg-primary/10 text-primary transition-colors"
              }}
          >
              <Users className="h-5 w-5" />
              <span className="sr-only">Dashboard</span>
          </Link>
        </Tooltip>

        <Tooltip content="Goals" position="right">
          <Link
              to="/goals"
              className="group relative flex h-11 w-11 items-center justify-center rounded-lg text-sidebar-foreground/60 transition-colors hover:bg-sidebar-accent hover:text-sidebar-foreground"
              activeProps={{
                className: "group relative flex h-11 w-11 items-center justify-center rounded-lg bg-primary/10 text-primary transition-colors"
              }}
          >
              <Goal className="h-5 w-5" />
              <span className="sr-only">Goals</span>
          </Link>
        </Tooltip>

        <Tooltip content="Settings" position="right">
          <Link
              to="/settings"
              className="group relative flex h-11 w-11 items-center justify-center rounded-lg text-sidebar-foreground/60 transition-colors hover:bg-sidebar-accent hover:text-sidebar-foreground"
              activeProps={{
                className: "group relative flex h-11 w-11 items-center justify-center rounded-lg bg-primary/10 text-primary transition-colors"
              }}
          >
              <Settings className="h-5 w-5" />
              <span className="sr-only">Settings</span>
          </Link>
        </Tooltip>
        </nav>

        {/* Theme Toggle */}
        <Tooltip
          content={theme === "dark" ? "Switch to Light Mode" : "Switch to Dark Mode"}
          position="right"
        >
          <button
          onClick={onToggleTheme}
          className="flex h-11 w-11 items-center justify-center rounded-lg text-sidebar-foreground/60 transition-colors hover:bg-sidebar-accent hover:text-sidebar-foreground"
          >
          {theme === "dark" ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
          <span className="sr-only">Toggle theme</span>
          </button>
        </Tooltip>
    </div>
);

export default NavigationSidebar;