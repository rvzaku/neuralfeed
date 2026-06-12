// Web Share API with clipboard fallback. Returns "shared" | "copied" | "failed".
export async function shareUrl(url: string, title: string): Promise<"shared" | "copied" | "failed"> {
  if (typeof navigator !== "undefined" && navigator.share) {
    try {
      await navigator.share({ title, url });
      return "shared";
    } catch {
      // user cancelled or unsupported payload — fall through to clipboard
    }
  }
  try {
    await navigator.clipboard.writeText(url);
    return "copied";
  } catch {
    return "failed";
  }
}
