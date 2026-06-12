"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { authLogin, authRegister } from "@/lib/api";
import { clearSession, getEmail, setSession } from "@/lib/auth";

export default function LoginPage() {
  const router = useRouter();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const currentEmail = typeof window !== "undefined" ? getEmail() : null;

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      const fn = mode === "login" ? authLogin : authRegister;
      const res = await fn(email, password);
      setSession(res.access_token, res.email);
      router.push("/");
    } catch (err: unknown) {
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(detail ?? "Something went wrong — try again.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="min-h-dvh flex items-center justify-center bg-background px-4">
      <div className="w-full max-w-sm space-y-6">
        <div className="text-center space-y-1">
          <h1 className="font-serif text-2xl font-semibold">NeuralFeed</h1>
          <p className="text-sm text-muted-foreground">
            {mode === "login" ? "Sign in to your account" : "Create an account"}
          </p>
        </div>

        {currentEmail && (
          <div className="rounded-lg border border-border p-3 text-sm flex items-center justify-between">
            <span className="truncate text-muted-foreground">Signed in as {currentEmail}</span>
            <button
              className="text-primary font-medium ml-3 shrink-0"
              onClick={() => {
                clearSession();
                router.refresh();
              }}
            >
              Sign out
            </button>
          </div>
        )}

        <form onSubmit={onSubmit} className="space-y-3">
          <input
            type="email"
            required
            autoComplete="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full min-h-[44px] rounded-lg border border-border bg-background px-3 text-base focus:outline-none focus:ring-2 focus:ring-primary"
          />
          <input
            type="password"
            required
            minLength={8}
            autoComplete={mode === "login" ? "current-password" : "new-password"}
            placeholder="Password (min 8 characters)"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full min-h-[44px] rounded-lg border border-border bg-background px-3 text-base focus:outline-none focus:ring-2 focus:ring-primary"
          />
          {error && <p className="text-sm text-red-600 dark:text-red-400">{error}</p>}
          <button
            type="submit"
            disabled={busy}
            className="w-full min-h-[44px] rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors disabled:opacity-60"
          >
            {busy ? "Please wait…" : mode === "login" ? "Sign in" : "Create account"}
          </button>
        </form>

        <p className="text-center text-sm text-muted-foreground">
          {mode === "login" ? (
            <>
              No account?{" "}
              <button className="text-primary font-medium" onClick={() => setMode("register")}>
                Register
              </button>
            </>
          ) : (
            <>
              Already registered?{" "}
              <button className="text-primary font-medium" onClick={() => setMode("login")}>
                Sign in
              </button>
            </>
          )}
        </p>
      </div>
    </main>
  );
}
