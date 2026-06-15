---
name: responsive-frontend
description: >
  Use this skill whenever a user asks to build, design, create, or scaffold any frontend page,
  web interface, landing page, dashboard, form, or UI component using HTML, CSS, and JavaScript.
  Trigger for: "build me a page", "create a website", "design a UI", "make a responsive layout",
  "frontend for X", "web page for X", "build a dashboard", "create a form", "design a component".
  Always applies desktop-first responsive design and a clean light theme color palette.
  Use even when the user doesn't explicitly say "responsive" or "light theme" — these are non-negotiable defaults.
---

# Responsive Frontend Skill

Build polished, desktop-first responsive pages using semantic HTML, modern CSS, and vanilla JavaScript. Every page follows a carefully curated **light theme** and degrades gracefully down to mobile.

---

## Non-Negotiable Defaults

| Rule | Value |
|---|---|
| Design direction | **Desktop-first** — design for wide screens, then add breakpoints going down |
| Theme | **Light** — white/off-white backgrounds, dark text, soft shadows |
| Layout | CSS Grid + Flexbox hybrid |
| Interactivity | Vanilla JS (no frameworks unless asked) |
| Output | Single `.html` file (inline CSS + JS) unless instructed otherwise |

---

## Design Process

### 1. Understand the Brief
Before writing a line of code, confirm:
- **What is the page for?** (landing page, dashboard, form, portfolio, etc.)
- **Who is the user?** (developer, customer, internal tool user, etc.)
- **What is the page's single job?** (sign up, explore, compare, submit, etc.)

If the brief is vague, pick a concrete subject yourself and state your assumption.

### 2. Plan the Token System

Define a compact token system before coding. Write it as a comment block at the top of your `<style>`:

```css
/* === TOKEN SYSTEM ===
   Background:  #FFFFFF (page), #F8F9FA (surface), #F1F3F5 (subtle)
   Text:        #1A1A2E (primary), #4A4A68 (secondary), #9A9AB0 (muted)
   Accent:      #4F46E5 (primary), #7C3AED (secondary), #E0E7FF (tint)
   Border:      #E2E6EA (default), #CBD3DA (strong)
   Shadow:      0 1px 3px rgba(0,0,0,.08), 0 4px 16px rgba(0,0,0,.06)
   Radius:      4px (tight), 8px (card), 16px (large), 9999px (pill)
   Spacing:     4 | 8 | 12 | 16 | 24 | 32 | 48 | 64 | 96px
*/
```

You may adjust the accent color to suit the subject, but **always keep backgrounds light and text dark**.

### 3. Responsive Breakpoints (Desktop-First)

Always write base styles for `≥1280px`, then override downward:

```css
/* Base = Desktop (≥1280px) */
.container { max-width: 1200px; padding: 0 48px; }

/* Tablet (≤1024px) */
@media (max-width: 1024px) { ... }

/* Mobile L (≤768px) */
@media (max-width: 768px) { ... }

/* Mobile S (≤480px) */
@media (max-width: 480px) { ... }
```

---

## Light Theme Color Palette

### Approved Palette Groups

**Neutral Base** (always use for backgrounds/text):
```
Page BG:     #FFFFFF
Surface:     #F8F9FA
Subtle:      #F1F3F5
Border:      #E2E6EA
Text Primary:   #1A1A2E
Text Secondary: #4A4A68
Text Muted:     #9A9AB0
```

**Accent Options** (pick one set per project):

| Mood | Primary | Secondary | Tint |
|---|---|---|---|
| Professional / Indigo | `#4F46E5` | `#7C3AED` | `#E0E7FF` |
| Fresh / Teal | `#0D9488` | `#0891B2` | `#CCFBF1` |
| Warm / Amber | `#D97706` | `#B45309` | `#FEF3C7` |
| Bold / Rose | `#E11D48` | `#BE185D` | `#FFE4E6` |
| Nature / Emerald | `#059669` | `#047857` | `#D1FAE5` |

**Forbidden in light theme**: black backgrounds (`#000`, `#111`), neon colors, pure white text on white, low-contrast combinations. Always target WCAG AA minimum (4.5:1 contrast ratio for body text).

---

## Structural Patterns

### Page Shell

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Page Title</title>
  <style>
    /* === TOKEN SYSTEM === */
    /* === RESET === */
    /* === BASE === */
    /* === LAYOUT === */
    /* === COMPONENTS === */
    /* === UTILITIES === */
    /* === RESPONSIVE === */
  </style>
</head>
<body>
  <header>...</header>
  <main>...</main>
  <footer>...</footer>
  <script>/* JS here */</script>
</body>
</html>
```

### CSS Reset (include always)

```css
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html { font-size: 16px; scroll-behavior: smooth; }
body { font-family: system-ui, -apple-system, 'Segoe UI', sans-serif;
       background: #FFFFFF; color: #1A1A2E; line-height: 1.6; }
img, video { max-width: 100%; display: block; }
a { color: inherit; text-decoration: none; }
button { cursor: pointer; border: none; background: none; font: inherit; }
```

### Typography Scale

```css
/* Display / Hero */
.text-hero    { font-size: clamp(2rem, 5vw, 3.5rem); font-weight: 800; line-height: 1.1; }
/* Headings */
.text-h1      { font-size: clamp(1.75rem, 3vw, 2.5rem); font-weight: 700; }
.text-h2      { font-size: clamp(1.375rem, 2.5vw, 1.875rem); font-weight: 600; }
.text-h3      { font-size: clamp(1.125rem, 2vw, 1.375rem); font-weight: 600; }
/* Body */
.text-lg      { font-size: 1.125rem; line-height: 1.7; }
.text-base    { font-size: 1rem;     line-height: 1.65; }
.text-sm      { font-size: 0.875rem; line-height: 1.6; }
.text-xs      { font-size: 0.75rem;  line-height: 1.5; }
```

### Grid & Container

```css
.container     { width: 100%; max-width: 1200px; margin: 0 auto; padding: 0 48px; }
.grid-2        { display: grid; grid-template-columns: repeat(2, 1fr); gap: 32px; }
.grid-3        { display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px; }
.grid-4        { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; }
.flex-center   { display: flex; align-items: center; justify-content: center; }
.flex-between  { display: flex; align-items: center; justify-content: space-between; }

@media (max-width: 1024px) {
  .container { padding: 0 32px; }
  .grid-4    { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 768px) {
  .container { padding: 0 20px; }
  .grid-2, .grid-3, .grid-4 { grid-template-columns: 1fr; }
}
```

---

## Component Library

### Navigation

```css
.nav {
  position: sticky; top: 0; z-index: 100;
  background: rgba(255,255,255,0.9); backdrop-filter: blur(12px);
  border-bottom: 1px solid #E2E6EA;
  padding: 0 48px; height: 64px;
  display: flex; align-items: center; justify-content: space-between;
}
.nav-logo { font-weight: 700; font-size: 1.25rem; color: #1A1A2E; }
.nav-links { display: flex; gap: 32px; }
.nav-links a { color: #4A4A68; font-size: 0.9375rem; transition: color .2s; }
.nav-links a:hover { color: #4F46E5; }
.nav-cta { /* primary button styles */ }

@media (max-width: 768px) {
  .nav-links { display: none; }
  /* Add hamburger menu with JS toggle */
}
```

### Cards

```css
.card {
  background: #FFFFFF;
  border: 1px solid #E2E6EA;
  border-radius: 12px;
  padding: 28px;
  box-shadow: 0 1px 3px rgba(0,0,0,.06);
  transition: box-shadow .2s, transform .2s;
}
.card:hover {
  box-shadow: 0 8px 24px rgba(0,0,0,.1);
  transform: translateY(-2px);
}
```

### Buttons

```css
.btn {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 10px 22px; border-radius: 8px;
  font-size: 0.9375rem; font-weight: 600;
  transition: all .2s;
}
.btn-primary {
  background: #4F46E5; color: #FFFFFF;
  box-shadow: 0 1px 3px rgba(79,70,229,.3);
}
.btn-primary:hover { background: #4338CA; box-shadow: 0 4px 12px rgba(79,70,229,.4); }
.btn-secondary {
  background: #F1F3F5; color: #1A1A2E;
  border: 1px solid #E2E6EA;
}
.btn-secondary:hover { background: #E2E6EA; }
.btn-ghost { color: #4F46E5; }
.btn-ghost:hover { background: #E0E7FF; }
/* Sizes */
.btn-sm { padding: 7px 16px; font-size: 0.875rem; }
.btn-lg { padding: 14px 32px; font-size: 1rem; border-radius: 10px; }
```

### Forms

```css
.form-group { display: flex; flex-direction: column; gap: 6px; }
.form-label { font-size: 0.875rem; font-weight: 500; color: #4A4A68; }
.form-input {
  padding: 10px 14px;
  border: 1.5px solid #E2E6EA; border-radius: 8px;
  font-size: 0.9375rem; color: #1A1A2E;
  background: #FFFFFF;
  transition: border-color .2s, box-shadow .2s;
  outline: none;
}
.form-input:focus {
  border-color: #4F46E5;
  box-shadow: 0 0 0 3px rgba(79,70,229,.12);
}
.form-input::placeholder { color: #9A9AB0; }
.form-hint { font-size: 0.8125rem; color: #9A9AB0; }
.form-error { font-size: 0.8125rem; color: #E11D48; }
```

### Badges & Tags

```css
.badge {
  display: inline-flex; align-items: center;
  padding: 3px 10px; border-radius: 9999px;
  font-size: 0.75rem; font-weight: 600; letter-spacing: .02em;
}
.badge-primary { background: #E0E7FF; color: #4F46E5; }
.badge-success { background: #D1FAE5; color: #059669; }
.badge-warning { background: #FEF3C7; color: #D97706; }
.badge-danger  { background: #FFE4E6; color: #E11D48; }
```

### Section Spacing

```css
.section     { padding: 96px 0; }
.section-sm  { padding: 64px 0; }
.section-lg  { padding: 128px 0; }
@media (max-width: 768px) {
  .section    { padding: 64px 0; }
  .section-sm { padding: 40px 0; }
  .section-lg { padding: 80px 0; }
}
```

---

## JavaScript Patterns

### Mobile Nav Toggle

```javascript
const hamburger = document.querySelector('.hamburger');
const navLinks = document.querySelector('.nav-links');
hamburger?.addEventListener('click', () => {
  navLinks.classList.toggle('open');
  hamburger.setAttribute('aria-expanded',
    navLinks.classList.contains('open'));
});
```

### Smooth Scroll Spy

```javascript
const sections = document.querySelectorAll('section[id]');
const navLinks = document.querySelectorAll('.nav-links a[href^="#"]');
window.addEventListener('scroll', () => {
  let current = '';
  sections.forEach(s => {
    if (window.scrollY >= s.offsetTop - 100) current = s.id;
  });
  navLinks.forEach(a => {
    a.classList.toggle('active', a.getAttribute('href') === `#${current}`);
  });
}, { passive: true });
```

### Scroll Reveal Animation

```javascript
const observer = new IntersectionObserver(entries => {
  entries.forEach(e => {
    if (e.isIntersecting) { e.target.classList.add('visible'); }
  });
}, { threshold: 0.15 });
document.querySelectorAll('.reveal').forEach(el => observer.observe(el));
```

```css
.reveal { opacity: 0; transform: translateY(24px); transition: opacity .6s, transform .6s; }
.reveal.visible { opacity: 1; transform: none; }
@media (prefers-reduced-motion: reduce) { .reveal { opacity: 1; transform: none; } }
```

### Form Validation

```javascript
function validateForm(form) {
  let valid = true;
  form.querySelectorAll('[required]').forEach(field => {
    const group = field.closest('.form-group');
    const error = group?.querySelector('.form-error');
    if (!field.value.trim()) {
      field.style.borderColor = '#E11D48';
      if (error) error.style.display = 'block';
      valid = false;
    } else {
      field.style.borderColor = '';
      if (error) error.style.display = 'none';
    }
  });
  return valid;
}
```

---

## Accessibility Checklist

Before delivering any page, verify:
- [ ] All images have `alt` attributes
- [ ] Color contrast meets WCAG AA (4.5:1 body, 3:1 large text)
- [ ] Interactive elements are keyboard-focusable
- [ ] Focus styles are visible (never `outline: none` without replacement)
- [ ] Form inputs have associated `<label>` elements
- [ ] Buttons have descriptive text or `aria-label`
- [ ] `lang` attribute on `<html>`
- [ ] Skip-to-content link for keyboard users (on multi-section pages)

---

## Quality Bar

Every delivered page must:
1. Render correctly at 1440px, 1024px, 768px, and 375px
2. Have zero horizontal scroll on any screen size
3. Use semantic HTML (`<header>`, `<main>`, `<section>`, `<article>`, `<footer>`)
4. Have a consistent vertical rhythm (spacing from the 4px scale)
5. Never use `!important` unless overriding a third-party library
6. Have CSS organized: tokens → reset → base → layout → components → utilities → responsive

---

## Reference Files

See `references/` for deeper patterns:
- `layout-patterns.md` — Hero, features, pricing, testimonials, CTA section templates
- `animation-guide.md` — Motion principles and keyframe library

---

## Quick Decision Guide

| Task | Pattern to Use |
|---|---|
| Landing page | Hero + Features grid + CTA + Footer |
| Dashboard | Sticky sidebar + Top bar + Card grid + Data table |
| Form page | Centered card layout + Step indicators + Inline validation |
| Blog/Article | Single column prose + Table of contents sidebar |
| Portfolio | Masonry or 3-col grid + Lightbox overlay |
| Pricing | 3-col card comparison + Toggle (monthly/annual) |