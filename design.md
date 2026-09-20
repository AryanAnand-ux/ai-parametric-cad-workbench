# Design System
## AI Parametric CAD Workbench

**Version:** 1.0  
**Last Updated:** September 2026  

---

## 1. Design Philosophy

The workbench follows an **engineering-first aesthetic** — precision, clarity, and minimal distraction. Inspired by professional CAD tools (SolidWorks, Rhino) and modern design tools (Figma, Linear). The palette is warm neutrals with high-contrast accents, avoiding aggressive primary colors.

**Key Principles:**
- **Precision over decoration** — every UI element serves a functional purpose
- **Warmth without softness** — warm gray tones instead of cold dark mode
- **Responsive depth** — micro-animations and shadows create tactile feedback
- **Information density** — workbench surfaces are compact; landing page is spacious

---

## 2. Color Palette

### 2.1 Core Brand Colors
```css
--color-bg-primary:     #F6F6F0;  /* Warm off-white — main surface */
--color-bg-secondary:   #EEEEE8;  /* Slightly darker — panel backgrounds */
--color-bg-tertiary:    #E4E4DC;  /* Hover/active states */

--color-text-primary:   #2C2828;  /* Near-black warm — primary text */
--color-text-secondary: #474040;  /* Medium warm gray — secondary text */
--color-text-muted:     #99908F;  /* Light warm gray — placeholders, hints */

--color-border:         #D8D4CE;  /* Panel borders */
--color-border-strong:  #C8C0BC;  /* Stronger borders / dividers */

--color-accent:         #474040;  /* Primary CTA background */
--color-accent-hover:   #2C2828;  /* CTA hover state */
```

### 2.2 Status / Semantic Colors
```css
--color-success:        #3D7A5E;  /* Green — success states */
--color-error:          #C0392B;  /* Red — error messages */
--color-warning:        #C07A2B;  /* Amber — warning states */
--color-info:           #2B72C0;  /* Blue — informational */

--color-generating:     #8B7355;  /* Brown-amber — active generation */
```

### 2.3 Viewer / 3D Background Themes
| Theme | Value | Description |
|-------|-------|-------------|
| `atelier_sand` | `#E8E4DC` | Default warm sand |
| `studio_white` | `#F5F5F2` | Clean studio look |
| `midnight_blue` | `#1A2030` | Dark presentation mode |
| `forest_floor` | `#2A3020` | Deep green |

---

## 3. Typography

### 3.1 Font Stack
```css
font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
```
Inter is loaded via Google Fonts. Fallback chain ensures rendering on all platforms.

### 3.2 Type Scale
| Role | Size | Weight | Letter-spacing |
|------|------|--------|----------------|
| Hero headline | 56–72px | 300 (Light) | -0.02em |
| Section headline | 32–40px | 300 | -0.01em |
| Card title | 18–20px | 400 | 0 |
| Body text | 15–16px | 400 | 0 |
| Label / UI text | 11–13px | 500 | 0.06–0.10em |
| Code / monospace | 12–13px | 400 | 0 (monospace) |

### 3.3 Monospace
```css
font-family: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace;
```
Used in: code inspector modal, parameter values, coordinate readouts.

---

## 4. Spacing & Layout

### 4.1 Spacing Scale (8px base grid)
```css
--space-1:  4px
--space-2:  8px
--space-3: 12px
--space-4: 16px
--space-5: 20px
--space-6: 24px
--space-8: 32px
--space-10: 40px
--space-12: 48px
```

### 4.2 Workbench Layout
```
┌─────────────────────────────────────────────────────────────┐
│  HEADER (48px)                                               │
│  [Brand Logo] [Nav Tabs: View/Params/Chat/Export] [User]     │
├───────────┬─────────────────────────────────┬───────────────┤
│ SIDEBAR   │     3D VIEWPORT                 │               │
│ (280px)   │     (flex-grow, min 400px)       │               │
│ Projects  │     Viewer3D.jsx                │               │
│ History   │     ViewportToolbar.jsx          │               │
│           │     (bottom toolbar)             │               │
│           │                                 │               │
├───────────┴─────────────────────────────────┴───────────────┤
│  PROMPT BAR (64px)                                           │
│  [Prompt Input ─────────────────────────────] [Generate Btn] │
└─────────────────────────────────────────────────────────────┘
```

### 4.3 Border Radius
```css
--radius-sm:  4px   /* Buttons, chips */
--radius-md:  8px   /* Cards, panels */
--radius-lg:  12px  /* Modals, drawers */
--radius-xl:  16px  /* Hero cards */
--radius-full: 9999px /* Pills, badges */
```

---

## 5. Components

### 5.1 Buttons

**Primary (Generate / CTA)**
```css
background: var(--color-accent);     /* #474040 */
color: #FFFFFF;
border-radius: var(--radius-sm);
padding: 10px 20px;
font-size: 13px;
font-weight: 500;
letter-spacing: 0.06em;
transition: background 0.15s ease;
```

**Secondary (Ghost)**
```css
background: transparent;
border: 1px solid var(--color-border);
color: var(--color-text-secondary);
```

**Danger**
```css
background: var(--color-error);
color: white;
```

### 5.2 Navigation Tabs (Header)
- Segmented control style — compact, no individual button padding waste
- Active tab: solid background `--color-accent`, white text
- Inactive: transparent, `--color-text-secondary`
- Transition: 0.15s ease on background

### 5.3 Parameter Slider
- Custom `<input type="range">` with styled thumb and track
- Track: `--color-border` background; filled portion via CSS gradient
- Min/max labels displayed below slider
- Debounced recompute: 300ms after last drag event

### 5.4 Modals
- Backdrop: `rgba(0, 0, 0, 0.4)` blur overlay
- Panel: `--color-bg-primary` background, `--radius-lg` corners
- Max width: 560px (auth/share), 800px (code inspector)
- Animation: fade + scale-up from 0.95 → 1.0

### 5.5 Error Banner
- Sticky below header
- Background: `rgba(192, 57, 43, 0.08)` (red tint)
- Left border: 3px solid `--color-error`
- Dismiss button: × character

### 5.6 3D Viewer Material Presets
| Material | Appearance |
|----------|-----------|
| `cad_gray` | Matte warm gray — default engineering look |
| `metallic` | Silver PBR metallic |
| `plastic_white` | Matte white plastic |
| `transparent` | Glass-like translucent |
| `wireframe` | Black edges only |

---

## 6. Landing Page Design

The landing page is a **full-scroll marketing page** with these sections:
1. **Hero** — Large headline + CTA button + 3D model preview
2. **Disciplines** — Grid of engineering disciplines (Mechanical, Aerospace, Civil, etc.)
3. **Feature Pillars** — Three-column feature highlights
4. **Workflow** — Step-by-step animation showing the generation flow
5. **Gallery Preview** — Masonry grid of community models
6. **FAQ** — Accordion with common questions
7. **Footer** — Links + social

Landing page uses a **larger type scale** and more generous spacing (`--space-12` between sections) compared to the compact workbench.

---

## 7. Micro-Animations

| Element | Animation | Duration |
|---------|-----------|----------|
| Buttons | `background` color transition | 150ms |
| Modal open | `opacity` 0→1, `scale` 0.95→1 | 200ms |
| Tab switch | `background` transition | 150ms |
| Error banner appear | `slideDown` keyframe | 250ms |
| Parameter slider thumb | `transform scale` on hover | 150ms |
| Generation progress bar | `width` CSS transition | 300ms |
| Landing hero text | Stagger fade-in on mount | 400ms delay steps |

---

## 8. Responsive Design

The workbench is **desktop-first** (minimum 1024px recommended):
- Below 768px: sidebar collapses, toolbar goes vertical
- Below 480px: prompt bar stacks vertically

Landing page is fully responsive:
- Desktop (>1200px): 3-column feature grid
- Tablet (768–1200px): 2-column grid
- Mobile (<768px): single column, stacked sections

---

## 9. Accessibility

- All interactive elements have `aria-label` attributes
- Focus rings visible on keyboard navigation (`:focus-visible` styles)
- Contrast ratio: text on backgrounds meets WCAG AA (4.5:1)
- Modals trap focus and are dismissible with `Escape`
- 3D viewer has text fallback for non-WebGL environments

---

## 10. Icon System

- No icon library — uses Unicode symbols and CSS-drawn icons for minimal bundle size
- Where SVG is needed (export format icons, toolbar buttons), inline SVG in JSX
- Avoid emoji in UI — use semantic symbols only
