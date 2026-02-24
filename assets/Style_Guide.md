# Alauda Style Guide

The visual design system for Alauda — colors, typography, logos, and usage rules. For brand narrative, messaging, and voice, see `Brand.md`.

---

## 1. Colors

### Primary — Alauda Blue

| Name | Hex | CSS Token | Role |
|---|---|---|---|
| Blue 700 | `#1A6A9A` | `--alauda-blue-deeper` | Dark headings, text links (WCAG AA on white) |
| Blue 600 | `#2A8ABF` | `--alauda-blue-dark` | Hover states, pressed buttons |
| **Blue 500** | **`#3BAEE4`** | **`--alauda-blue`** | **Primary brand — CTAs, logo, links** |
| Blue 400 | `#6DC4EC` | `--alauda-blue-light` | Illustrations, icons on dark backgrounds |
| Blue 200 | `#B8E2F6` | `--alauda-blue-lighter` | Borders, dividers, tags |
| Blue 50 | `#EAF6FC` | `--alauda-blue-wash` | Tinted backgrounds, callout boxes |

**Alauda Blue details:** RGB 59, 174, 228 · HSL 199°, 76%, 56% · CMYK 74, 24, 0, 11 · Pantone PMS 299 C

### Neutral — Slate

| Name | Hex | CSS Token | Role |
|---|---|---|---|
| Slate 950 | `#0B0F14` | `--neutral-950` | Pure dark backgrounds |
| Slate 900 | `#111827` | `--neutral-900` | Primary text, dark mode background |
| Slate 800 | `#1E293B` | `--neutral-800` | Dark cards, elevated surfaces |
| Slate 700 | `#334155` | `--neutral-700` | Secondary text |
| Slate 600 | `#475569` | `--neutral-600` | Body text |
| Slate 500 | `#64748B` | `--neutral-500` | Captions, labels, muted text |
| Slate 400 | `#94A3B8` | `--neutral-400` | Placeholder, secondary on dark |
| Slate 300 | `#CBD5E1` | `--neutral-300` | Borders, rules |
| Slate 200 | `#E2E8F0` | `--neutral-200` | Subtle borders |
| Slate 100 | `#F1F5F9` | `--neutral-100` | Page background, alternating sections |
| Slate 50 | `#F8FAFC` | `--neutral-50` | Card background |
| White | `#FFFFFF` | `--white` | Cards, content areas |

### Accent

| Name | Hex | CSS Token | Role |
|---|---|---|---|
| Navy | `#0F2B46` | `--accent-navy` | Hero backgrounds, footers, slide covers |
| Navy Light | `#1B3F5E` | `--accent-navy-light` | Elevated dark surfaces |
| Teal | `#14B8A6` | `--accent-teal` | AI product accent, data visualization |
| Teal Light | `#5EEAD4` | `--accent-teal-light` | Charts, highlights on dark backgrounds |
| Teal Wash | `#E6FAF7` | `--accent-teal-wash` | AI-related callout backgrounds |

### Semantic / UI State

| Name | Hex | Light Hex | CSS Token | Usage |
|---|---|---|---|---|
| Success | `#16A34A` | `#DCFCE7` | `--success` | Uptime, success states |
| Warning | `#EAB308` | `#FEF9C3` | `--warning` | Cautions, pending states |
| Error | `#DC2626` | `#FEE2E2` | `--error` | Errors, critical alerts |
| Info | `#3BAEE4` | `#EAF6FC` | `--info` | Informational banners |

---

## 2. Color Usage by Material

### Website
- Hero/header backgrounds → Navy `#0F2B46`
- Content areas → White `#FFFFFF`
- Alternating sections → Slate 100 `#F1F5F9`
- CTAs, links → Alauda Blue `#3BAEE4`
- Body text → Slate 900 `#111827`
- AI-related sections → Teal accent `#14B8A6`

### Slide Decks
- Cover & divider slides → Navy `#0F2B46`
- Content slides → White background
- Highlight bars, icons → Alauda Blue `#3BAEE4`
- Callout boxes → Blue 50 wash `#EAF6FC`
- Chart primary → Blue 700 `#1A6A9A`
- Chart secondary → Teal `#14B8A6`

### Business / Name Cards
- Front → White `#FFFFFF`; logo & accents in Alauda Blue; name in Slate 900; contacts in Slate 500
- Back → Navy `#0F2B46`; Alauda Blue icon; tagline in Slate 400; URL in Blue 400 `#6DC4EC`

### Documents & Reports
- Body text → Slate 900 `#111827`
- Section headings → Blue 700 `#1A6A9A`
- Accent rules & bars → Alauda Blue `#3BAEE4`
- Callout boxes → Blue 50 `#EAF6FC` with 3px Blue left border
- Table borders → Slate 300 `#CBD5E1`

### Dark Mode
| Layer | Hex |
|---|---|
| Page background | `#0B0F14` |
| Surface | `#111827` |
| Elevated | `#1E293B` |
| Borders | `#334155` |
| Primary text | `#F8FAFC` |
| Secondary text | `#94A3B8` |
| Brand accent | `#3BAEE4` |
| AI accent | `#14B8A6` |

---

## 3. Color Do's and Don'ts

### Do
- Use Navy (`#0F2B46`) for dark hero backgrounds — warmer and more branded than pure black
- Pair Alauda Blue with white text on buttons and CTAs
- Use Blue 700 (`#1A6A9A`) for body text links — meets WCAG AA contrast on white
- Reserve Teal accent for AI-related content to differentiate ACP from Alauda AI
- Use Blue 50 wash (`#EAF6FC`) sparingly for callout boxes and featured sections
- Maintain at least 60% white/neutral space in any composition

### Don't
- Use Alauda Blue (`#3BAEE4`) for body text on white — fails WCAG AA contrast
- Place Alauda Blue text on light blue backgrounds — insufficient contrast
- Use more than 2 brand colors in a single section or slide
- Mix Navy and Slate 900 as adjacent backgrounds — too similar, visual confusion
- Use saturated colors for large text blocks — stick to neutrals
- Apply gradients to the logo

---

## 4. Typography

### Font Stacks

**Inter — Headings & UI**
- Stack: `'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif`
- Weights: 300 (Light), 400 (Regular), 500 (Medium), 600 (Semibold), 700 (Bold), 800 (ExtraBold)
- Use: Website headings, UI elements, buttons, navigation, documents
- Source: Google Fonts (OFL, free for commercial use)

**Manrope — Display / Hero**
- Stack: `'Manrope', 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif`
- Weights: 600, 700, 800
- Use: Large hero headlines, display numbers, marketing callouts
- Source: Google Fonts (OFL)

**JetBrains Mono — Code & Data**
- Stack: `'JetBrains Mono', 'SF Mono', 'Cascadia Mono', 'Consolas', monospace`
- Weights: 400, 500
- Use: Code snippets, metrics (99.99%), hex values, data labels
- Source: Google Fonts (OFL)

### CSS Tokens

```css
:root {
  --font-heading: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  --font-body:    'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  --font-display: 'Manrope', 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  --font-mono:    'JetBrains Mono', 'SF Mono', 'Cascadia Mono', 'Consolas', monospace;
}
```

### Google Fonts Loading

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
```

### Type Scale

| Token | Size | Weight | Tracking | Notes |
|---|---|---|---|---|
| `hero` | 52–56px | 800 | -0.03em | Hero displays |
| `h1` | 40–48px | 700–800 | -0.02em | Page titles |
| `h2` | 32–36px | 700 | -0.01em | Section headers |
| `h3` | 24–28px | 600–700 | -0.005em | Subsections |
| `h4` | 18–20px | 600 | 0 | Card headers |
| `body-lg` | 18px | 400 | 0 | Lead body copy |
| `body` | 16px | 400 | 0 | Standard body |
| `body-sm` | 14px | 400–500 | 0 | Secondary copy |
| `caption` | 12–13px | 500 | 0.01em | Labels, tags |
| `overline` | 11–12px | 600–700 | 0.1em | Uppercase labels (e.g., "PLATFORM OVERVIEW") |
| `mono` | 13–14px | 400–500 | 0 | Code, metrics, hex values |

### System Font Fallbacks (Slides & Print)

| Platform | Font | Mono Pair | Use |
|---|---|---|---|
| macOS | SF Pro Display (`-apple-system`) | SF Mono | Keynote, Pages, print PDFs |
| Windows | Segoe UI | Cascadia Mono | PowerPoint, Word, print PDFs |
| Cross-platform | Inter (install from rsms.me/inter) | JetBrains Mono | Embedded in documents |

### Font Specs by Material

| Material | Role | Font | Weights |
|---|---|---|---|
| Website | Headings | Inter | 600, 700, 800 |
| Website | Body | Inter | 400, 500 |
| Website | Code / Data | JetBrains Mono | 400, 500 |
| Slides (macOS) | Headings | SF Pro Display | Semibold, Bold |
| Slides (macOS) | Body | SF Pro Text | Regular, Medium |
| Slides (Windows) | Headings | Segoe UI | Semibold, Bold |
| Slides (Windows) | Body | Segoe UI | Regular, Light |
| Name Cards | Name & Title | System default | Bold, Medium |
| Name Cards | Contact | System default | Regular |
| Documents | Headings | Inter or system | 700 |
| Documents | Body | Inter or system | 400 |
| Documents | Data callouts | JetBrains Mono | 400 |

---

## 5. Logo

### Variants

| Variant | Format | Files | Use |
|---|---|---|---|
| **Horizontal (recommended)** | SVG, PNG 1x, PNG 4x | `Logo/primary/svg/alauda-logo-horizontal-*.svg` | Website headers, slide decks, documents |
| Vertical | SVG, PNG 1x, PNG 4x | `Logo/primary/svg/alauda-logo-vertical-*.svg` | Tall layouts, banners, square placements |
| Wordmark Horizontal | SVG, PNG 1x, PNG 4x | `Logo/primary/svg/alauda-wordmark-horizontal-*.svg` | When "Alauda" text is needed (requires Inter) |
| Wordmark Vertical | SVG, PNG 1x, PNG 4x | `Logo/primary/svg/alauda-wordmark-vertical-*.svg` | Stacked wordmark layout |
| Icon (bird mark) | SVG, PNG 1x, PNG 4x | `Logo/primary/svg/alauda-icon-*.svg` | Favicons, app icons, social avatars |
| Favicon | ICO | `Logo/primary/favicon.ico` | Browser tab icon |

### Color Variants

Each logo variant comes in three colors:
- **Blue** (`-blue`) — on light/white backgrounds
- **Black** (`-black`) — on light/white backgrounds
- **White** (`-white`) — on dark backgrounds (Navy, Slate 900, Alauda Blue)

### Chinese Variants (for alauda.cn)

| Layout | Files |
|---|---|
| Compact | `Logo/chinese/svg/alauda-cn-compact-*.svg` |
| Horizontal | `Logo/chinese/svg/alauda-cn-horizontal-*.svg` |

Both available in SVG, PNG 1x, and PNG 4x in blue, black, and white.

### Logo Rules
- Never apply gradients to the logo
- Use blue or black variants on light backgrounds only
- Use white variant on dark backgrounds only
- Maintain clear space around the logo

---

## 6. Key Color Combinations

| Context | Background | Foreground | Example |
|---|---|---|---|
| Website hero / Slide cover | Navy `#0F2B46` | White + Blue 400 `#6DC4EC` | Hero headlines |
| Content cards / Data points | White `#FFFFFF` | Slate 900 + Alauda Blue | Stat callouts, case studies |
| Feature sections / Callouts | Blue 50 `#EAF6FC` | Blue 700 `#1A6A9A` | "500+ Enterprises", "2M+ vCores" |
| AI product / Dark mode | Slate 900 `#111827` | White + Teal `#14B8A6` | Alauda AI sections |
| Proof points / Testimonials | Slate 100 `#F1F5F9` | Slate 700 `#334155` | Recognition, quotes |
| CTAs / Name card back | Alauda Blue `#3BAEE4` | White | Buttons, card reverse |
