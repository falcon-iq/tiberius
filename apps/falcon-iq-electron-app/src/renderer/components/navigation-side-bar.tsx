import { Users, Goal, Settings, Sun, Moon } from "lucide-react"
import { Link } from "@tanstack/react-router"

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
        <Link
            to="/"
            className="group relative flex h-11 w-11 items-center justify-center rounded-lg text-sidebar-foreground/60 transition-colors hover:bg-sidebar-accent hover:text-sidebar-foreground"
            activeProps={{
              className: "group relative flex h-11 w-11 items-center justify-center rounded-lg bg-primary/10 text-primary transition-colors"
            }}
            title="Dashboard"
        >
            <Users className="h-5 w-5" />
            <span className="sr-only">Dashboard</span>
        </Link>

        <Link
            to="/goals"
            className="group relative flex h-11 w-11 items-center justify-center rounded-lg text-sidebar-foreground/60 transition-colors hover:bg-sidebar-accent hover:text-sidebar-foreground"
            activeProps={{
              className: "group relative flex h-11 w-11 items-center justify-center rounded-lg bg-primary/10 text-primary transition-colors"
            }}
            title="Goals"
        >
            <Goal className="h-5 w-5" />
            <span className="sr-only">Goals</span>
        </Link>

        <Link
            to="/settings"
            className="group relative flex h-11 w-11 items-center justify-center rounded-lg text-sidebar-foreground/60 transition-colors hover:bg-sidebar-accent hover:text-sidebar-foreground"
            activeProps={{
              className: "group relative flex h-11 w-11 items-center justify-center rounded-lg bg-primary/10 text-primary transition-colors"
            }}
            title="Settings"
        >
            <Settings className="h-5 w-5" />
            <span className="sr-only">Settings</span>
        </Link>
        </nav>

        {/* Theme Toggle */}
        <button
        onClick={onToggleTheme}
        className="flex h-11 w-11 items-center justify-center rounded-lg text-sidebar-foreground/60 transition-colors hover:bg-sidebar-accent hover:text-sidebar-foreground"
        title={theme === "dark" ? "Switch to Light Mode" : "Switch to Dark Mode"}
        >
        {theme === "dark" ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
        <span className="sr-only">Toggle theme</span>
        </button>
    </div>
);

export default NavigationSidebar;