"use client";

// Login-first gate: without a stored token, every page except /login
// redirects immediately — no waiting for an API 401. The backend still
// enforces auth server-side (AUTH_REQUIRED); this is the UX layer.

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { getToken } from "@/lib/auth";

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [checked, setChecked] = useState(false);

  useEffect(() => {
    if (pathname.startsWith("/login")) {
      setChecked(true);
      return;
    }
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    setChecked(true);
  }, [pathname, router]);

  // Avoid flashing protected content before the check runs
  if (!checked && !pathname.startsWith("/login")) return null;
  return <>{children}</>;
}
