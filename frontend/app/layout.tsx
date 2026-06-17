import type { Metadata, Viewport } from "next";
import { Geist, Geist_Mono, Fraunces } from "next/font/google";
import "./globals.css";
import { ThemeProvider } from "@/components/providers/ThemeProvider";
import { QueryProvider } from "@/components/providers/QueryProvider";
import { AuthGuard } from "@/components/providers/AuthGuard";
import { ServiceWorkerRegister } from "@/components/providers/ServiceWorkerRegister";

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });
// Editorial display serif for titles/headings — the signature that separates
// NeuralFeed from generic all-sans AI dashboards (app-feedback: "not AI-looking").
const fraunces = Fraunces({
  variable: "--font-display",
  subsets: ["latin"],
  axes: ["opsz", "SOFT"],
});

export const metadata: Metadata = {
  metadataBase: new URL("https://neuralfeed.vercel.app"),
  title: "NeuralFeed — AI News Intelligence",
  description: "Your personal AI news dashboard. Signal, not noise.",
  applicationName: "NeuralFeed",
  appleWebApp: { capable: true, title: "NeuralFeed", statusBarStyle: "default" },
  openGraph: {
    title: "NeuralFeed — AI News Intelligence",
    description: "The signal worth your time in AI — ranked, finite, and sent straight to you.",
    siteName: "NeuralFeed",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "NeuralFeed — AI News Intelligence",
    description: "The signal worth your time in AI — ranked, finite, and sent straight to you.",
  },
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#fafaf5" },
    { media: "(prefers-color-scheme: dark)", color: "#16140f" },
  ],
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${geistSans.variable} ${geistMono.variable} ${fraunces.variable} antialiased min-h-screen`}>
        <ThemeProvider>
          <QueryProvider>
            <AuthGuard>{children}</AuthGuard>
          </QueryProvider>
        </ThemeProvider>
        <ServiceWorkerRegister />
      </body>
    </html>
  );
}
