"use client";

// V7: "Today" is folded into the Feed as a top-10 block. This route is kept only
// as a redirect so old links / bookmarks land on the Feed instead of 404-ing.

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function TodayPage() {
  const router = useRouter();
  useEffect(() => {
    router.replace("/");
  }, [router]);
  return null;
}
