# Anti-"AI-slop" Redesign Plan — Feed (in-place, Next.js)

> Problem (user, 2026-06-16): deployed site "still looks AI-centric / slop / unattractive"
> despite the warm palette + serif already being live. Root cause is NOT tokens — it's
> **visual busyness**: a confetti of colored pills + dense, boxed cards. Premium editorial
> design is the opposite: severe colour restraint, calm list, strong type hierarchy.

## Diagnosis — the AI-slop tells currently in `FeedCard`
1. Rainbow of filled colored chips: stars(amber) velocity(emerald) votes(orange)
   comments(sky) downloads(violet) likes(rose) + 11-colour topic tags + colored source
   badge + "% match" indigo pill + amber "Unread" badge + trending chip. Too many colours.
2. Every item is a boxed `rounded-xl border bg-card` with `hover:border-primary/40` — busy,
   "appy", not editorial.
3. Literal AI tells: a `✦` sparkle on the why-line; loud "% match" badge.
4. Over-dense: 4 stacked metadata zones before you reach the title.

## Principles (the fix)
- **One accent + one signal colour only.** Indigo accent (unread dot, focus, active
  feedback) + the heat ramp (amber→orange→red) as the single "hotness" signal. EVERYTHING
  else is ink / muted / hairline. No filled colour pills for traction or topics.
- **Calm list, not boxes.** Hairline divider between items; generous whitespace; whole row
  tappable. No per-card border box, no hover border-colour.
- **Type does the work.** Fraunces serif title (larger), then ONE quiet muted meta line,
  then context line, then a single restrained traction line.
- **Remove tells.** Kill `✦`; "% match" → quiet mono `97` next to a label; "Unread" badge →
  the accent dot only.

## Changes
1. `FeedView`: card container `space-y-3` → `divide-y divide-border/60` (list, not stack).
2. `FeedCard`: wrapper → padded list row (`py-5`, no border/rounded/bg, subtle read-dim).
   - Meta line: source icon+name, author, publish date — all muted, one line.
   - Title: `.font-display` ~18px, hover → foreground (not primary).
   - Traction: muted text + small icon (★ 71.2k · +412 today · 222 HN · 141 comments),
     NO filled colour pills; velocity "+today" gets a single subtle green tint, nothing else.
   - Relevance: quiet `REL 97` mono, muted; not an indigo pill.
   - Topic tags: hairline outline chips, single muted tone (one colour, lowercase).
   - Heat: keep `HeatBadge` (the one colour signal), top-right.
   - Remove `✦`; unread = accent dot at left, no badge.
3. `SourceBadge`: icon + label in MUTED ink (remove per-source colour fills); keep the icon.
4. Keep all data/logic (feedback, bookmark, share, image, engagement freshness) intact.

## Acceptance
F1 (premium, not AI), F2 (font) → re-verify on deploy. Feed reads calm, mostly monochrome,
with colour only on heat + the unread dot. Build green; push; Vercel redeploy.
