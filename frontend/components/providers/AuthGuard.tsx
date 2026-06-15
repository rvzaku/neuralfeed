"use client";

// Login-first gate: without a stored token, every page except /login
// redirects immediately — no waiting for an API 401. The backend still
// enforces auth server-side (AUTH_REQUIRED); this is the UX layer.

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { clearSession, getToken, isGuest } from "@/lib/auth";

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [checked, setChecked] = useState(false);
  const [guest, setGuest] = useState(false);

  useEffect(() => {
    if (pathname.startsWith("/login")) {
      setChecked(true);
      return;
    }
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    setGuest(isGuest());
    setChecked(true);
  }, [pathname, router]);

  // Avoid flashing protected content before the check runs
  if (!checked && !pathname.startsWith("/login")) return null;

  return (
    <>
      {guest && (
        <div className="sticky top-0 z-50 flex items-center justify-center gap-3 bg-foreground px-4 py-2 text-center text-xs font-medium text-background">
          <span>👀 Guest preview — read-only. Sign in to rate, save, and personalize.</span>
          <button
            onClick={() => {
              clearSession();
              router.replace("/login");
            }}
            className="underline underline-offset-2 hover:opacity-80"
          >
            Sign in
          </button>
        </div>
      )}
      {children}
    </>
  );
}
