import type { MetadataRoute } from "next";

// PWA manifest — makes NeuralFeed installable to the home screen (mobile-first
// thesis). Icons are SVG with purpose "any maskable"; the warm paper background
// matches the light-theme --background so the splash never flashes a cold white.
export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "NeuralFeed — AI News Intelligence",
    short_name: "NeuralFeed",
    description: "Your personal AI news dashboard. Signal, not noise.",
    start_url: "/",
    display: "standalone",
    background_color: "#fafaf5",
    theme_color: "#4f46e5",
    icons: [
      { src: "/icon.svg", sizes: "any", type: "image/svg+xml", purpose: "any" },
      { src: "/icon.svg", sizes: "any", type: "image/svg+xml", purpose: "maskable" },
    ],
  };
}
