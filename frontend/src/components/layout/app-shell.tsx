import { NavLink, Outlet } from "react-router-dom";
import { Dumbbell, History, LayoutDashboard, Settings, Zap, Moon, Sun } from "lucide-react";
import { cn } from "@/lib/utils";
import { useTheme } from "@/providers/theme";
import { Button } from "@/components/ui/button";

const NAV = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/exercises", label: "Exercises", icon: Dumbbell },
  { to: "/sessions", label: "History", icon: History },
  { to: "/settings", label: "Settings", icon: Settings },
];

function BrandMark() {
  return (
    <div className="flex items-center gap-2.5 px-2">
      <span className="grid size-9 place-items-center rounded-xl bg-primary text-primary-foreground">
        <Zap className="size-5" />
      </span>
      <div>
        <p className="text-sm font-bold leading-none tracking-tight">AI-GYM</p>
        <p className="mt-1 text-[11px] leading-none text-muted-foreground">Intelligent Coaching</p>
      </div>
    </div>
  );
}

/** Application frame: icon rail (desktop) + top bar (mobile) + routed content. */
export function AppShell() {
  const { theme, toggle } = useTheme();
  return (
    <div className="min-h-screen bg-background">
      {/* Desktop sidebar */}
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-64 flex-col border-r border-border/60 bg-card/60 backdrop-blur md:flex">
        <div className="flex h-16 items-center border-b border-border/60 px-4">
          <BrandMark />
        </div>
        <nav className="flex-1 space-y-1 p-3">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground",
                  isActive && "bg-primary/10 text-primary hover:bg-primary/10 hover:text-primary",
                )
              }
            >
              <item.icon className="size-4" />
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="border-t border-border/60 p-3">
          <Button variant="ghost" size="sm" className="w-full justify-start" onClick={toggle}>
            {theme === "dark" ? <Sun /> : <Moon />}
            {theme === "dark" ? "Light mode" : "Dark mode"}
          </Button>
        </div>
      </aside>

      {/* Mobile top bar */}
      <header className="sticky top-0 z-30 flex h-14 items-center justify-between border-b border-border/60 bg-background/90 px-4 backdrop-blur md:hidden">
        <BrandMark />
        <div className="flex items-center gap-1">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                cn(
                  "rounded-lg p-2 text-muted-foreground transition-colors hover:text-foreground",
                  isActive && "bg-primary/10 text-primary",
                )
              }
            >
              <item.icon className="size-5" />
            </NavLink>
          ))}
        </div>
      </header>

      <main className="md:pl-64">
        <div className="mx-auto w-full max-w-6xl px-4 py-6 md:px-8 md:py-8">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
