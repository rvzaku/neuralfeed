"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Rss, Bookmark, Database, Users, Settings } from "lucide-react";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { href: "/",          label: "Feed",     icon: Rss },
  { href: "/bookmarks", label: "Saved",    icon: Bookmark },
  { href: "/sources",   label: "Sources",  icon: Database },
  { href: "/accounts",  label: "Accounts", icon: Users },
  { href: "/settings",  label: "Settings", icon: Settings },
];

export function MobileNav() {
  const pathname = usePathname();
  return (
    <nav className="md:hidden fixed bottom-0 left-0 right-0 z-20 bg-background/90 backdrop-blur-sm border-t border-border">
      <div className="flex">
        {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
          const active = pathname === href;
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex-1 flex flex-col items-center justify-center gap-0.5 min-h-[56px] text-[9px] font-medium transition-colors",
                active ? "text-primary" : "text-muted-foreground hover:text-foreground"
              )}
            >
              <Icon className="h-5 w-5" />
              {label}
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
