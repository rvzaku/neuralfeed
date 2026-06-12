"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Newspaper, Compass, Database, Settings } from "lucide-react";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { href: "/",         label: "Feed",     icon: Newspaper },
  { href: "/discover", label: "Discover", icon: Compass },
  { href: "/sources",  label: "Sources",  icon: Database },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function MobileNav() {
  const pathname = usePathname();
  return (
    <nav
      className="md:hidden fixed bottom-3 inset-x-3 z-20 pb-[env(safe-area-inset-bottom)]"
      aria-label="Primary"
    >
      <div className="flex rounded-full border border-border bg-card/90 backdrop-blur-md shadow-lg shadow-black/10 px-1.5 py-1.5">
        {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
          const active = pathname === href;
          return (
            <Link
              key={href}
              href={href}
              aria-current={active ? "page" : undefined}
              className={cn(
                "flex-1 flex items-center justify-center gap-1.5 min-h-[44px] rounded-full text-[11px] font-semibold transition-all duration-200",
                active
                  ? "bg-gradient-brand text-white shadow-md"
                  : "text-muted-foreground hover:text-foreground active:scale-95"
              )}
            >
              <Icon className="h-[18px] w-[18px]" strokeWidth={active ? 2.4 : 1.9} />
              {/* Label only on the active tab keeps the dock compact */}
              <span className={cn(!active && "sr-only")}>{label}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
