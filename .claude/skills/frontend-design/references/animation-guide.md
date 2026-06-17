# Animation Guide

## Principles

1. **Motion serves function** — animate to guide attention, confirm actions, or show relationships. Never for decoration.
2. **Speed is respect** — entrances 200–400ms, exits faster (150–250ms). Never exceed 600ms for UI transitions.
3. **Easing is personality** — use `ease-out` for elements entering, `ease-in` for leaving, `ease-in-out` for continuous.
4. **One choreography, not chaos** — stagger related items; don't animate everything at once.
5. **Always respect `prefers-reduced-motion`**.

```css
/* Global reduced motion override — always include */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: .01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: .01ms !important;
  }
}
```

---

## Keyframe Library

### Fade In Up (scroll reveal)
```css
@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(20px); }
  to   { opacity: 1; transform: translateY(0); }
}
.animate-fadeInUp { animation: fadeInUp .5s ease-out both; }
```

### Fade In (simple)
```css
@keyframes fadeIn {
  from { opacity: 0; }
  to   { opacity: 1; }
}
.animate-fadeIn { animation: fadeIn .4s ease-out both; }
```

### Scale In (modal/popover)
```css
@keyframes scaleIn {
  from { opacity: 0; transform: scale(.94); }
  to   { opacity: 1; transform: scale(1); }
}
.animate-scaleIn { animation: scaleIn .2s ease-out both; }
```

### Slide Down (dropdown)
```css
@keyframes slideDown {
  from { opacity: 0; transform: translateY(-8px); }
  to   { opacity: 1; transform: translateY(0); }
}
.animate-slideDown { animation: slideDown .2s ease-out both; }
```

### Pulse (loading indicator)
```css
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50%       { opacity: .4; }
}
.animate-pulse { animation: pulse 1.6s ease-in-out infinite; }
```

### Spin (spinner)
```css
@keyframes spin {
  to { transform: rotate(360deg); }
}
.animate-spin { animation: spin .7s linear infinite; }
```

### Shimmer (skeleton loader)
```css
@keyframes shimmer {
  from { background-position: -200% 0; }
  to   { background-position:  200% 0; }
}
.skeleton {
  background: linear-gradient(90deg, #F1F3F5 25%, #E2E6EA 50%, #F1F3F5 75%);
  background-size: 200% 100%;
  animation: shimmer 1.4s ease-in-out infinite;
  border-radius: 6px;
}
```

---

## Staggered List Entrance

```css
.stagger-list > * { opacity: 0; animation: fadeInUp .45s ease-out both; }
.stagger-list > *:nth-child(1) { animation-delay: 0ms; }
.stagger-list > *:nth-child(2) { animation-delay: 80ms; }
.stagger-list > *:nth-child(3) { animation-delay: 160ms; }
.stagger-list > *:nth-child(4) { animation-delay: 240ms; }
.stagger-list > *:nth-child(5) { animation-delay: 320ms; }
.stagger-list > *:nth-child(6) { animation-delay: 400ms; }
```

For longer lists, generate delays with JS:
```javascript
document.querySelectorAll('.stagger-list > *').forEach((el, i) => {
  el.style.animationDelay = `${i * 70}ms`;
});
```

---

## Hover Micro-interactions

```css
/* Lift on hover (cards) */
.hover-lift { transition: transform .2s ease-out, box-shadow .2s ease-out; }
.hover-lift:hover { transform: translateY(-3px); box-shadow: 0 12px 32px rgba(0,0,0,.1); }

/* Arrow nudge (links) */
.hover-arrow { display: inline-flex; align-items: center; gap: 4px; }
.hover-arrow::after { content: '→'; transition: transform .2s; }
.hover-arrow:hover::after { transform: translateX(4px); }

/* Underline slide (nav links) */
.hover-underline { position: relative; }
.hover-underline::after {
  content: ''; position: absolute; bottom: -2px; left: 0;
  width: 0; height: 2px; background: currentColor;
  transition: width .2s ease-out;
}
.hover-underline:hover::after { width: 100%; }
```

---

## Page Load Sequence

For hero sections, orchestrate entrance with CSS delays:

```css
.hero-eyebrow  { animation: fadeInUp .5s ease-out .1s both; }
.hero-headline { animation: fadeInUp .5s ease-out .2s both; }
.hero-sub      { animation: fadeInUp .5s ease-out .35s both; }
.hero-actions  { animation: fadeInUp .5s ease-out .5s both; }
```

---

## Toast / Notification

```css
.toast {
  position: fixed; bottom: 24px; right: 24px; z-index: 9999;
  background: #1A1A2E; color: white;
  padding: 12px 20px; border-radius: 10px;
  font-size: 0.9375rem; font-weight: 500;
  box-shadow: 0 8px 24px rgba(0,0,0,.2);
  animation: slideUp .25s ease-out;
}
@keyframes slideUp {
  from { opacity: 0; transform: translateY(12px); }
  to   { opacity: 1; transform: translateY(0); }
}
```

```javascript
function showToast(message, duration = 3000) {
  const toast = document.createElement('div');
  toast.className = 'toast';
  toast.textContent = message;
  document.body.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(8px)';
    toast.style.transition = 'opacity .2s, transform .2s';
    setTimeout(() => toast.remove(), 200);
  }, duration);
}
```