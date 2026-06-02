import Link from "next/link";
import { useRouter } from "next/router";
import { useEffect, useState } from "react";
import { supabase } from "../lib/supabaseClient";
import Button from "./Button";

const navItems = [
  { label: "Home", shortLabel: "Home", href: "/" },
  { label: "Cardio Lab", shortLabel: "Cardio", href: "/cardio-lab" },
  { label: "HYROX Planner", shortLabel: "HYROX", href: "/form" },
  { label: "Plan", shortLabel: "Plan", href: "/plan" },
  { label: "Dashboard", shortLabel: "Dash", href: "/dashboard" },
  { label: "Diet", shortLabel: "Diet", href: "/diet" },
  { label: "AI Coach", shortLabel: "AI", href: "/ai-coach" },
];

export default function Navbar() {
  const router = useRouter();
  const [user, setUser] = useState(null);
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  useEffect(() => {
    if (!supabase) {
      return;
    }

    supabase.auth.getUser().then(({ data }) => {
      setUser(data.user);
    });

    const { data: listener } = supabase.auth.onAuthStateChange(
      (_event, session) => {
        setUser(session?.user || null);
      }
    );

    return () => {
      listener.subscription.unsubscribe();
    };
  }, []);

  useEffect(() => {
    setIsMenuOpen(false);
  }, [router.pathname]);

  async function handleLogout() {
    if (supabase) {
      await supabase.auth.signOut();
    }
    setUser(null);
    setIsMenuOpen(false);
    router.push("/");
  }

  function isActive(href) {
    if (href === "/") {
      return router.pathname === "/";
    }
    return router.pathname.startsWith(href);
  }

  return (
    <header className="sticky top-0 z-40 border-b border-white/10 bg-carbon/85 backdrop-blur-xl">
      <nav className="mx-auto flex max-w-7xl items-center justify-between px-5 py-4">
        <Link href="/" className="group flex items-center gap-3">
          <span className="flex h-9 w-9 items-center justify-center rounded-lg border border-volt/40 bg-volt text-sm font-black text-carbon transition group-hover:scale-105">
            Z
          </span>
          <div>
            <p className="text-sm font-black uppercase tracking-[0.22em] text-white">
              Zone 5
            </p>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-white/50">
              Performance Lab
            </p>
          </div>
        </Link>

        <div className="hidden items-center gap-6 text-sm font-bold text-white/70 lg:flex">
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`transition hover:text-volt ${
                isActive(item.href) ? "text-volt" : ""
              }`}
            >
              {item.label}
            </Link>
          ))}
        </div>

        <div className="hidden items-center gap-3 lg:flex">
          {user ? (
            <Button onClick={handleLogout} variant="secondary">
              Logout
            </Button>
          ) : (
            <>
              <Button href="/login" variant="secondary">
                Login
              </Button>
              <Button href="/signup">Signup</Button>
            </>
          )}
        </div>

        <button
          type="button"
          onClick={() => setIsMenuOpen((current) => !current)}
          aria-expanded={isMenuOpen}
          aria-label="Open navigation menu"
          className="flex min-h-12 items-center gap-3 rounded-lg border border-white/15 bg-white/5 px-4 text-sm font-black uppercase tracking-[0.14em] text-white transition hover:border-volt/40 hover:bg-white/10 lg:hidden"
        >
          <span className="hidden sm:inline">{isMenuOpen ? "Close" : "Menu"}</span>
          <span className="flex h-6 w-6 flex-col justify-center gap-1.5">
            <span
              className={`h-0.5 w-6 rounded-full bg-volt transition ${
                isMenuOpen ? "translate-y-2 rotate-45" : ""
              }`}
            />
            <span
              className={`h-0.5 w-6 rounded-full bg-volt transition ${
                isMenuOpen ? "opacity-0" : ""
              }`}
            />
            <span
              className={`h-0.5 w-6 rounded-full bg-volt transition ${
                isMenuOpen ? "-translate-y-2 -rotate-45" : ""
              }`}
            />
          </span>
        </button>
      </nav>

      {isMenuOpen && (
        <div className="border-t border-white/10 bg-carbon/95 px-5 py-4 shadow-2xl backdrop-blur-xl lg:hidden">
          <div className="mx-auto max-w-7xl">
            <div className="grid overflow-hidden rounded-lg border border-volt/20 bg-black/35 sm:grid-cols-2 lg:grid-cols-4">
              {navItems.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`min-h-14 border-b border-white/10 px-4 py-4 text-sm font-black uppercase tracking-[0.12em] transition last:border-b-0 sm:border-r sm:last:border-r-0 lg:border-b-0 ${
                    isActive(item.href)
                      ? "bg-volt text-carbon"
                      : "text-white/70 hover:bg-white/5 hover:text-volt"
                  }`}
                >
                  {item.label}
                </Link>
              ))}
            </div>

            <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:justify-end">
              {user ? (
                <Button onClick={handleLogout} variant="secondary">
                  Logout
                </Button>
              ) : (
                <>
                  <Button href="/login" variant="secondary">
                    Login
                  </Button>
                  <Button href="/signup">Signup</Button>
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </header>
  );
}
