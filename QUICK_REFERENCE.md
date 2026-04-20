# Enterprise UI — Quick Reference Card

## Color Palette

```css
/* Neutrals (Primary) */
--gray-50:  #F9FAFB  /* Background */
--gray-100: #F3F4F6  /* Hover states */
--gray-200: #E5E7EB  /* Borders */
--gray-300: #D1D5DB  /* Disabled */
--gray-400: #9CA3AF  /* Placeholder */
--gray-500: #6B7280  /* Secondary text */
--gray-600: #4B5563  /* Body text */
--gray-700: #374151  /* Headings */
--gray-900: #111827  /* Primary text */

/* Accent (Minimal use) */
--blue-500: #3B82F6  /* Primary actions */
--blue-600: #2563EB  /* Hover */

/* Status */
--green-500: #10B981  /* Positive */
--red-500:   #EF4444  /* Negative */
--amber-500: #F59E0B  /* Warning */
```

## Typography Scale

```css
/* Sizes */
11px  /* Uppercase labels, metadata */
13px  /* Helper text, captions */
14px  /* Body text, buttons (BASE) */
16px  /* Section headers */
24px  /* KPI values */
28px  /* Prediction values */

/* Weights */
400   /* Body text */
500   /* Labels, buttons */
600   /* Headings, values */

/* Font Stack */
-apple-system, BlinkMacSystemFont, "Segoe UI", "Inter", sans-serif
```

## Spacing System (8px base)

```css
4px   /* xs  - Icon-text gap */
8px   /* sm  - Inline elements */
16px  /* md  - Card padding */
24px  /* lg  - Section spacing */
32px  /* xl  - Major sections */
48px  /* xxl - Page-level */
```

## Component Heights

```css
Header:     60px
KPI Card:   88px
Button:     40px
Input:      40px
Tab:        48px
Table Row:  48px
Chart:      280px
```

## Border Radius

```css
4px  /* Small (badges) */
6px  /* Medium (buttons, cards) */
8px  /* Large (modals) */
```

## Shadows

```css
--shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05)
--shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1)
--shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1)
```

## Button Styles

```css
/* Primary */
background: var(--blue-500)
color: white
height: 40px
padding: 0 20px
border-radius: 6px

/* Secondary */
background: white
color: var(--gray-700)
border: 1px solid var(--gray-300)

/* Ghost */
background: transparent
color: var(--gray-600)
```

## Input Styles

```css
height: 40px
padding: 0 12px
border: 1px solid var(--gray-300)
border-radius: 6px
font-size: 14px

/* Focus */
border-color: var(--blue-500)
box-shadow: 0 0 0 3px var(--blue-50)
```

## Table Styles

```css
/* Header */
background: var(--gray-50)
font-size: 12px
font-weight: 500
padding: 12px

/* Cell */
font-size: 14px
padding: 12px
border-bottom: 1px solid var(--gray-100)

/* Hover */
background: var(--gray-50)
```

## Interaction States

```css
/* Hover */
Table Row:  gray-50 background
Button:     Darken 1 shade
Link:       Underline

/* Active */
Button:     Darken 2 shades
Tab:        blue-500 bottom border

/* Disabled */
opacity: 0.5
cursor: not-allowed

/* Focus */
border: blue-500
box-shadow: 0 0 0 3px blue-50
```

## Responsive Breakpoints

```css
/* Desktop */
1024px+  /* 4-col KPI, 2-col charts */

/* Tablet */
768-1023px  /* 2-col KPI, 1-col charts */

/* Mobile */
<767px  /* 1-col everything */
```

## Common Patterns

### KPI Card
```html
<div class="kpi-card">
  <div class="kpi-label">TOTAL SPEND</div>
  <div class="kpi-value">$47,892</div>
</div>
```

### Section Title
```html
<div class="section-title">Predictions</div>
```

### Status Message
```html
<p class="status-ok">✅ Success message</p>
<p class="status-err">❌ Error message</p>
```

### Data Table
```html
<table class="alloc-table">
  <thead>
    <tr><th>Campaign</th><th>Spend</th></tr>
  </thead>
  <tbody>
    <tr><td>Brand</td><td>$4,230</td></tr>
  </tbody>
</table>
```

## Accessibility Checklist

- [ ] Contrast ratio ≥ 4.5:1 (WCAG AA)
- [ ] Focus states visible (3px ring)
- [ ] Keyboard navigation works
- [ ] Semantic HTML (table, button, input)
- [ ] ARIA labels where needed

## Design Principles

1. **Clarity over decoration**
2. **Consistency over variety**
3. **Density over whitespace**
4. **Function over form**

## Reference Products

- Stripe Dashboard (color, typography)
- Linear (minimal aesthetic)
- Bloomberg Terminal (density)
- Airtable (tables)

## Files

- `enterprise_ui.css` — CSS source
- `UI_DESIGN_SPEC.md` — Full specs
- `IMPLEMENTATION_GUIDE.md` — How to use

---

**Print this card and keep it at your desk!**
