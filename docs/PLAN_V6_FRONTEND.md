# NeuralFeed V6 — Frontend (Lovable) Build Plan

> Lovable project `0bbfe28d-7e2a-489c-9c1c-5abe328fec0f`. Editorial direction locked in
> project knowledge. Backend/API unchanged. Source of truth for "what must render":
> `.dev-notes/frontend-acceptance.md`. This plan sequences the remaining build; each
> phase ends by updating that contract.

## Design invariants (hold every phase)
Warm ink palette · Fraunces serif titles + Inter UI + JetBrains Mono labels · no
gradients/glassmorphism/neon/emoji · hairline borders · finite/calm feed · subtle <200ms
motion, respect `prefers-reduced-motion` · 44px targets · accent indigo used sparingly.

---

## Phase 1 — Theme modes + iconography + color-coding & scores  ← THIS INCREMENT
Driven by: "add light and dark modes", "it does not have icons", and the v6
color-coding/score requirements.

### 1a. Light + Dark + System theme
- `ThemeProvider` (React context) with `light | dark | system`; persists to
  `localStorage`; applies/removes `.dark` on `<html>`; defaults to **system** and reacts
  to `matchMedia('(prefers-color-scheme: dark)')` live.
- A theme toggle control: a 3-way segmented control (Sun / Monitor / Moon icons) placed
  in the desktop sidebar footer and the mobile top bar; also surfaced in Settings.
- Both palettes already defined in `styles.css` — verify light mode is equally polished
  (warm paper, hairlines visible, heat ramp legible on light bg). Adjust contrast as
  needed. No FOUC: set initial theme via an inline `<head>` script before paint.

### 1b. Iconography (source brand icons + color-coding)
v6: "the website doesn't have any icons yet which will make it good enough" + color-coded
badges. Replace the text monogram with real per-source icons:
- Add `simple-icons` (brand SVGs) for GitHub, Reddit, Hacker News (Y Combinator), arXiv,
  Hugging Face, OpenAI, Anthropic, Google/DeepMind, Meta, Mistral, YouTube, X. Fallback to
  a tasteful lucide glyph (e.g. `Rss`, `FileText`) for unknown sources.
- A `SourceIcon` component: maps `source_id` → brand icon + that brand's signature color,
  rendered in a small rounded chip. Color is used *only* in the icon chip + traction
  glyphs, never to flood the card (keeps the restrained palette).
- Add meaningful lucide icons throughout: nav (already), section headers, empty states,
  actions, traction (Star, ArrowUp, MessageCircle, Download, TrendingUp), heat (Flame).

### 1c. Color-coding & score system (v6)
v6 wants traction + relevance to be *legible at a glance* and color-coded:
- **GitHub stars chip**: `★ 71.2k` + a green velocity chip `+412 today` (color-coded by
  momentum: grey→green as stars_today rises). Human-approximated formatting (71.2k, 1.8k).
- **Social/HN/Reddit**: upvote glyph + count, comment glyph + count.
- **HF**: download glyph + count. **Blogs**: honest recency or social proxy (no fake nums).
- **Relevance score (0–100)**: a small, quiet `REL 97` mono pill whose tint shifts on a
  cool→strong ramp (low=muted, high=accent-tinted) — a score the user can read but that
  doesn't shout.
- **Heat (0–4)**: keep the signature cool→warm pips + label + tooltip ("cross-source
  velocity right now"). Add a subtle heat-tinted left edge accent on heat≥3 items so hot
  stories are scannable in the list.
- **Topic tags**: small bordered chips; each topic family gets a consistent, restrained
  hue (e.g. Agents, Robotics, LLMs, Safety) — muted, not rainbow.
- Centralize all of this in a `lib/format.ts` (number/relative-time/heat-color/relevance-
  color/topic-color helpers) so it's consistent everywhere.

Acceptance (contract rows touched): F1/F2 (aesthetic+font), D1 (heat), C1/C2/C3 (traction),
new THEME + ICONS rows. Verify light AND dark at desktop + mobile.

---

## Phase 2 — Real API wiring + summary sheet
- Typed REST client (`lib/api.ts`) reading `VITE_API_URL`; React Query; graceful mock
  fallback. Feed, article summary, sources, topics endpoints.
- Login-first gate with **Continue as guest**; token in memory/localStorage; 401 → /login.
- Summary sheet: bottom sheet (mobile) / side panel (desktop), one ~5-min editorial
  summary (no sterile section headers), "Read at source →". Opens on card/title tap.
- Viewed items dim + drop on reload (dynamic feed).

## Phase 3 — Discover (+ Today) and Topics pages
- Discover: search + exploration; **Today** section with Day / Month / Year toggles;
  clicking opens summary sheet; no Topics duplication.
- Topics: own page; heat band + item count + one-line "why now" per topic; robotics/
  embodied-AI and agents first-class; accurate classification.

## Phase 4 — Sources + Settings
- Sources: list with enable/disable, add-source, per-source health + signal score; NO
  follow-targets.
- Settings: theme control + weighting sliders (Recency / Virality / Research / Company);
  NO ranking on/off, NO recap.

## Phase 5 — Polish, deploy, verify
- Skeletons, empty/error states, a11y pass, reduced-motion check, Lighthouse.
- Deploy (Lovable publish or export → Vercel); point at prod API; run `verify-deployed`
  against the new URL so every acceptance row goes PASS.

---

## Notes
- Curator rule holds: metadata only; images hotlinked, never stored.
- Never fabricate traction numbers — honest fallback per source.
- Each phase updates `.dev-notes/frontend-acceptance.md` statuses.
