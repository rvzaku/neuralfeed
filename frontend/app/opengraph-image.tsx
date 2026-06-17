import { ImageResponse } from "next/og";

// Polished link-preview card for shared NeuralFeed URLs. Built with the editorial
// palette (warm paper, indigo accent, serif wordmark) — no gradients, on-brand.
export const runtime = "edge";
export const alt = "NeuralFeed — AI News Intelligence";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default function OpengraphImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          padding: "80px",
          backgroundColor: "#fafaf5",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 24 }}>
          <div
            style={{
              width: 88,
              height: 88,
              borderRadius: 20,
              backgroundColor: "#4f46e5",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 60,
              fontWeight: 600,
              color: "#ffffff",
              fontFamily: "Georgia, serif",
            }}
          >
            N
          </div>
          <div style={{ fontSize: 64, fontWeight: 600, color: "#1c1a17", fontFamily: "Georgia, serif" }}>
            NeuralFeed
          </div>
        </div>
        <div style={{ marginTop: 40, fontSize: 40, color: "#57534e", maxWidth: 900 }}>
          The signal worth your time in AI — ranked, finite, and sent straight to you.
        </div>
        <div style={{ marginTop: 48, fontSize: 26, color: "#4f46e5", letterSpacing: 2 }}>
          SIGNAL · NOT NOISE
        </div>
      </div>
    ),
    { ...size }
  );
}
