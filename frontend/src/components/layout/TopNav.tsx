import { NavLink, Link } from "react-router-dom";
import { motion } from "framer-motion";
import { cn } from "../../lib/cn";
import { ThemeSwitcher } from "./ThemeSwitcher";
import { Activity } from "lucide-react";

const NAV_ITEMS = [
  { name: "Predict", path: "/predict" },
  { name: "Audio", path: "/audio" },
  { name: "Dashboard", path: "/dashboard" },
  { name: "About", path: "/about" },
];

export function TopNav() {
  return (
    <header className="sticky top-0 z-40 w-full border-b border-border bg-background/80 backdrop-blur-xl supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-16 items-center justify-between">
        <div className="flex gap-8 items-center">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2 group">
            <div className="p-1.5 rounded-lg bg-primary/10 text-primary group-hover:bg-primary group-hover:text-primary-foreground transition-colors duration-200">
              <Activity className="h-4 w-4" />
            </div>
            <span className="font-bold text-sm tracking-tight hidden sm:block">Parkinson's AI</span>
          </Link>

          {/* Nav links */}
          <nav className="hidden md:flex items-center gap-1">
            {NAV_ITEMS.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  cn(
                    "relative px-3 py-1.5 rounded-md text-sm font-medium transition-colors",
                    isActive
                      ? "text-foreground"
                      : "text-muted-foreground hover:text-foreground hover:bg-accent"
                  )
                }
              >
                {({ isActive }) => (
                  <>
                    {item.name}
                    {isActive && (
                      <motion.div
                        layoutId="nav-active-pill"
                        className="absolute inset-0 rounded-md bg-accent -z-10"
                        transition={{ type: "spring", stiffness: 380, damping: 30 }}
                      />
                    )}
                  </>
                )}
              </NavLink>
            ))}
          </nav>
        </div>

        <div className="flex items-center gap-3">
          <ThemeSwitcher />
        </div>
      </div>
    </header>
  );
}
