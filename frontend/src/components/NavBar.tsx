import { NavLink } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { ThemeToggle } from "./ThemeToggle";

const links = [
  { to: "/", label: "Home", end: true },
  { to: "/applications", label: "Applications" },
  { to: "/cvs", label: "CVs" },
  { to: "/settings", label: "Settings" },
];

export function NavBar() {
  const { user, logout } = useAuth();

  return (
    <nav className="border-b border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-900">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
        <div className="flex items-center gap-6">
          <span className="font-semibold text-slate-900 dark:text-slate-100">Application Tracker</span>
          <div className="flex gap-4">
            {links.map((link) => (
              <NavLink
                key={link.to}
                to={link.to}
                end={link.end}
                className={({ isActive }) =>
                  `text-sm font-medium ${
                    isActive
                      ? "text-indigo-600 dark:text-indigo-400"
                      : "text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-100"
                  }`
                }
              >
                {link.label}
              </NavLink>
            ))}
          </div>
        </div>
        <div className="flex items-center gap-3">
          {user && <span className="hidden text-sm text-slate-500 dark:text-slate-400 sm:inline">{user.email}</span>}
          <ThemeToggle />
          <button onClick={() => logout()} className="text-sm text-indigo-600 hover:underline dark:text-indigo-400">
            Sign out
          </button>
        </div>
      </div>
    </nav>
  );
}
