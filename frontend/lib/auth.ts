// Token storage + auth API (Phase 3.1). Backend runs with AUTH_REQUIRED=false
// until accounts exist, so logged-out users keep full access for now.

const TOKEN_KEY = "neuralfeed_token";
const EMAIL_KEY = "neuralfeed_email";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function getEmail(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(EMAIL_KEY);
}

export function setSession(token: string, email: string): void {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(EMAIL_KEY, email);
}

export function clearSession(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(EMAIL_KEY);
}
