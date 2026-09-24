import { Link, NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../auth";

const nav = [
  { to: "/", label: "Markets", end: true },
  { to: "/learn", label: "Learn" },
  { to: "/status", label: "Status" },
];

export default function Layout() {
  const { token } = useAuth();
  const links = token ? [...nav, { to: "/admin", label: "Admin" }] : [...nav, { to: "/login", label: "Log in" }];
  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-10 border-b border-indigo-100 bg-white/85 backdrop-blur">
        <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-x-6 gap-y-2 px-4 py-3">
          <Link to="/" className="text-lg font-extrabold tracking-tight">
            <span className="bg-linear-to-r from-indigo-600 to-fuchsia-600 bg-clip-text text-transparent">
              Market Forecasts
            </span>
            <span className="ml-2 rounded-full bg-amber-100 px-2 py-0.5 align-middle text-[10px] font-bold uppercase tracking-wide text-amber-700">
              Experimental
            </span>
          </Link>
          <nav className="flex gap-1">
            {links.map((n) => (
              <NavLink
                key={n.to}
                to={n.to}
                end={n.end}
                className={({ isActive }) =>
                  `rounded-full px-3 py-1.5 text-sm font-semibold transition ${
                    isActive ? "bg-indigo-600 text-white" : "text-slate-600 hover:bg-indigo-50"
                  }`
                }
              >
                {n.label}
              </NavLink>
            ))}
          </nav>
        </div>
      </header>

      <main className="mx-auto w-full max-w-5xl flex-1 px-4 py-6 sm:py-8">
        <Outlet />
      </main>

      <footer className="border-t border-indigo-100 bg-white/70">
        <p className="mx-auto max-w-5xl px-4 py-5 text-xs leading-relaxed text-slate-500">
          <strong className="text-slate-700">Experimental forecasts — not investment advice.</strong> Nothing here is a
          recommendation to buy or sell, and no result is guaranteed. Gold (GC=F) and silver (SI=F) are COMEX futures,
          not MCX spot prices. <Link to="/learn/disclaimer" className="font-semibold text-indigo-600 underline">Read the full disclaimer</Link>.
        </p>
      </footer>
    </div>
  );
}
