"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Eye, EyeOff, Lock, Mail, Sparkles } from "lucide-react";
import { authLogin, authRegister } from "@/lib/api";
import { setSession } from "@/lib/auth";
import { cn } from "@/lib/utils";

export default function LoginPage() {
  const router = useRouter();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (mode === "register" && password !== confirm) {
      setError("Passwords don't match.");
      return;
    }
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

  const inputCls =
    "w-full min-h-[48px] rounded-xl border border-border bg-background pl-10 pr-4 text-base " +
    "focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary/50 transition-shadow";

  return (
    <main className="min-h-dvh flex items-center justify-center bg-background px-4 relative overflow-hidden">
      {/* Soft brand glow backdrop */}
      <div
        className="absolute -top-32 left-1/2 -translate-x-1/2 h-72 w-[480px] rounded-full bg-primary/10 blur-3xl"
        aria-hidden
      />

      <div className="w-full max-w-sm space-y-7 relative">
        <div className="text-center space-y-2">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-foreground text-background shadow-sm">
            <Sparkles className="h-6 w-6" />
          </div>
          <h1 className="font-serif text-3xl font-bold text-foreground">NeuralFeed</h1>
          <p className="text-sm text-muted-foreground">
            {mode === "login"
              ? "Welcome back — sign in to your feed"
              : "Create your account to get started"}
          </p>
        </div>

        {/* Mode toggle */}
        <div className="flex rounded-full bg-muted p-1" role="tablist" aria-label="Auth mode">
          {([["login", "Sign in"], ["register", "Register"]] as const).map(([value, label]) => (
            <button
              key={value}
              role="tab"
              aria-selected={mode === value}
              onClick={() => { setMode(value); setError(null); }}
              className={cn(
                "flex-1 min-h-[40px] rounded-full text-sm font-semibold transition-all",
                mode === value
                  ? "bg-foreground text-background shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              )}
            >
              {label}
            </button>
          ))}
        </div>

        <form onSubmit={onSubmit} className="space-y-3.5 rounded-xl border border-border bg-card p-5 shadow-sm">
          <div className="relative">
            <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" aria-hidden />
            <input
              type="email"
              required
              autoComplete="email"
              placeholder="Email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className={inputCls}
              aria-label="Email"
            />
          </div>

          <div className="relative">
            <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" aria-hidden />
            <input
              type={showPassword ? "text" : "password"}
              required
              minLength={8}
              autoComplete={mode === "login" ? "current-password" : "new-password"}
              placeholder={mode === "register" ? "Password (min 8 characters)" : "Password"}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className={cn(inputCls, "pr-12")}
              aria-label="Password"
            />
            <button
              type="button"
              onClick={() => setShowPassword((v) => !v)}
              aria-label={showPassword ? "Hide password" : "Show password"}
              className="absolute right-2 top-1/2 -translate-y-1/2 p-2 text-muted-foreground hover:text-foreground transition-colors"
            >
              {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>

          {mode === "register" && (
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" aria-hidden />
              <input
                type={showPassword ? "text" : "password"}
                required
                minLength={8}
                autoComplete="new-password"
                placeholder="Confirm password"
                value={confirm}
                onChange={(e) => setConfirm(e.target.value)}
                className={inputCls}
                aria-label="Confirm password"
              />
            </div>
          )}

          {error && (
            <p role="alert" className="text-sm text-destructive bg-destructive/10 rounded-lg px-3 py-2">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={busy}
            className="w-full min-h-[48px] rounded-full bg-foreground text-background text-sm font-semibold shadow-md hover:opacity-90 active:scale-[0.99] transition-all disabled:opacity-60"
          >
            {busy ? "Please wait…" : mode === "login" ? "Sign in" : "Create account"}
          </button>
        </form>

        <p className="text-center text-xs text-muted-foreground">
          Private by design — your feed, your data, JWT-secured.
        </p>
      </div>
    </main>
  );
}
