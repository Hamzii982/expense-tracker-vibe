# Layout Patterns Reference

## Hero Section

```html
<section class="hero section-lg">
  <div class="container">
    <div class="hero-eyebrow">
      <span class="badge badge-primary">New · v2.0 Released</span>
    </div>
    <h1 class="text-hero hero-headline">
      The headline that says one clear thing
    </h1>
    <p class="text-lg hero-sub">
      Supporting sentence that answers "why should I care?"
      Two lines max. Plain language, no jargon.
    </p>
    <div class="hero-actions">
      <a href="#" class="btn btn-primary btn-lg">Primary CTA</a>
      <a href="#" class="btn btn-ghost btn-lg">Learn more →</a>
    </div>
    <div class="hero-social-proof">
      <span class="text-sm text-muted">Trusted by 10,000+ developers</span>
    </div>
  </div>
</section>
```

```css
.hero { background: linear-gradient(180deg, #F8F9FA 0%, #FFFFFF 60%); text-align: center; }
.hero-eyebrow { margin-bottom: 20px; }
.hero-headline { max-width: 760px; margin: 0 auto 24px; }
.hero-sub { max-width: 560px; margin: 0 auto 40px; color: #4A4A68; }
.hero-actions { display: flex; gap: 16px; justify-content: center; flex-wrap: wrap; margin-bottom: 32px; }
.hero-social-proof { color: #9A9AB0; }
```

---

## Features Grid

```html
<section class="section" id="features">
  <div class="container">
    <div class="section-header">
      <p class="section-eyebrow">Features</p>
      <h2 class="text-h2">Everything you need</h2>
      <p class="section-sub text-lg">Subtitle that adds context, not repetition.</p>
    </div>
    <div class="grid-3">
      <div class="feature-card card reveal">
        <div class="feature-icon">🚀</div>
        <h3 class="text-h3">Feature Name</h3>
        <p class="text-base">One or two sentences describing the benefit, not the mechanism.</p>
      </div>
      <!-- repeat × 6 -->
    </div>
  </div>
</section>
```

```css
.section-header { text-align: center; max-width: 640px; margin: 0 auto 64px; }
.section-eyebrow { font-size: 0.8125rem; font-weight: 700; letter-spacing: .08em;
                   text-transform: uppercase; color: #4F46E5; margin-bottom: 12px; }
.section-sub { color: #4A4A68; margin-top: 16px; }
.feature-icon { font-size: 2rem; margin-bottom: 16px; }
```

---

## Pricing Section (3-column)

```html
<section class="section pricing-section">
  <div class="container">
    <div class="section-header">
      <h2 class="text-h2">Simple pricing</h2>
      <div class="pricing-toggle">
        <span>Monthly</span>
        <button class="toggle" id="billingToggle" aria-pressed="false"></button>
        <span>Annual <span class="badge badge-success">Save 20%</span></span>
      </div>
    </div>
    <div class="pricing-grid">
      <div class="pricing-card card">
        <p class="pricing-tier">Starter</p>
        <p class="pricing-price"><span class="price-value">$0</span>/mo</p>
        <p class="pricing-desc">For individuals and side projects.</p>
        <ul class="pricing-features">
          <li>✓ 3 projects</li>
          <li>✓ 5GB storage</li>
        </ul>
        <a href="#" class="btn btn-secondary btn-lg" style="width:100%;justify-content:center;">Get started free</a>
      </div>
      <div class="pricing-card card pricing-featured">
        <span class="badge badge-primary" style="margin-bottom:12px;">Most popular</span>
        <!-- etc. -->
      </div>
    </div>
  </div>
</section>
```

```css
.pricing-toggle { display: flex; align-items: center; gap: 12px; justify-content: center; margin-top: 24px; }
.toggle { width: 44px; height: 24px; background: #E2E6EA; border-radius: 9999px; position: relative; transition: background .2s; }
.toggle.on { background: #4F46E5; }
.toggle::after { content:''; position:absolute; top:3px; left:3px; width:18px; height:18px;
                 background:#fff; border-radius:50%; transition:left .2s; }
.toggle.on::after { left:23px; }
.pricing-grid { display: grid; grid-template-columns: repeat(3,1fr); gap: 24px; align-items: start; }
.pricing-featured { border-color: #4F46E5; box-shadow: 0 8px 32px rgba(79,70,229,.15); }
.pricing-tier { font-size: 0.875rem; font-weight: 700; text-transform: uppercase; letter-spacing: .06em; color: #4A4A68; margin-bottom: 12px; }
.pricing-price { font-size: 2.5rem; font-weight: 800; margin-bottom: 8px; }
.pricing-features { list-style: none; display: flex; flex-direction: column; gap: 10px; margin: 24px 0; color: #4A4A68; font-size: 0.9375rem; }
@media (max-width: 768px) { .pricing-grid { grid-template-columns: 1fr; max-width: 420px; margin: 0 auto; } }
```

---

## Testimonials

```html
<section class="section testimonials-section" style="background:#F8F9FA;">
  <div class="container">
    <div class="section-header">
      <h2 class="text-h2">What people say</h2>
    </div>
    <div class="grid-3">
      <blockquote class="testimonial card reveal">
        <p class="testimonial-quote">"Specific quote that mentions a concrete outcome or feeling."</p>
        <footer class="testimonial-author">
          <div class="author-avatar">JD</div>
          <div>
            <p class="author-name">Jane Doe</p>
            <p class="author-role text-sm">Senior Engineer, Acme Co</p>
          </div>
        </footer>
      </blockquote>
    </div>
  </div>
</section>
```

```css
.testimonial-quote { font-size: 1.0625rem; line-height: 1.7; color: #1A1A2E; margin-bottom: 20px; font-style: italic; }
.testimonial-author { display: flex; align-items: center; gap: 12px; }
.author-avatar { width: 40px; height: 40px; border-radius: 50%; background: #E0E7FF;
                 color: #4F46E5; font-weight: 700; font-size: 0.875rem;
                 display: flex; align-items: center; justify-content: center; }
.author-name { font-weight: 600; font-size: 0.9375rem; }
.author-role { color: #9A9AB0; }
```

---

## CTA Banner

```html
<section class="section cta-section">
  <div class="container">
    <div class="cta-card">
      <h2 class="text-h2">Ready to get started?</h2>
      <p class="text-lg">One sentence that removes doubt and invites action.</p>
      <div class="cta-actions">
        <a href="#" class="btn btn-primary btn-lg">Start for free</a>
        <a href="#" class="btn btn-secondary btn-lg">Talk to sales</a>
      </div>
    </div>
  </div>
</section>
```

```css
.cta-card {
  background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);
  border-radius: 20px; padding: 72px 64px; text-align: center; color: white;
}
.cta-card h2 { color: white; margin-bottom: 16px; }
.cta-card p { color: rgba(255,255,255,.8); max-width: 480px; margin: 0 auto 40px; }
.cta-card .btn-secondary { background: rgba(255,255,255,.15); color: white; border-color: rgba(255,255,255,.3); }
.cta-card .btn-secondary:hover { background: rgba(255,255,255,.25); }
.cta-actions { display: flex; gap: 16px; justify-content: center; flex-wrap: wrap; }
@media (max-width: 768px) { .cta-card { padding: 48px 24px; } }
```

---

## Footer

```html
<footer class="footer">
  <div class="container">
    <div class="footer-top">
      <div class="footer-brand">
        <p class="nav-logo">Brand</p>
        <p class="text-sm footer-tagline">Short tagline. One line.</p>
      </div>
      <nav class="footer-nav">
        <div class="footer-col">
          <p class="footer-col-label">Product</p>
          <ul><li><a href="#">Features</a></li><li><a href="#">Pricing</a></li></ul>
        </div>
        <div class="footer-col">
          <p class="footer-col-label">Company</p>
          <ul><li><a href="#">About</a></li><li><a href="#">Blog</a></li></ul>
        </div>
      </nav>
    </div>
    <div class="footer-bottom">
      <p class="text-sm">&copy; 2025 Brand. All rights reserved.</p>
    </div>
  </div>
</footer>
```

```css
.footer { background: #F8F9FA; border-top: 1px solid #E2E6EA; padding: 64px 0 32px; }
.footer-top { display: flex; justify-content: space-between; gap: 48px; margin-bottom: 48px; flex-wrap: wrap; }
.footer-tagline { color: #9A9AB0; margin-top: 8px; max-width: 220px; }
.footer-nav { display: flex; gap: 64px; }
.footer-col-label { font-size: 0.75rem; font-weight: 700; text-transform: uppercase;
                    letter-spacing: .08em; color: #9A9AB0; margin-bottom: 16px; }
.footer-col ul { list-style: none; display: flex; flex-direction: column; gap: 10px; }
.footer-col a { color: #4A4A68; font-size: 0.9375rem; transition: color .2s; }
.footer-col a:hover { color: #4F46E5; }
.footer-bottom { border-top: 1px solid #E2E6EA; padding-top: 24px; color: #9A9AB0; }
@media (max-width: 768px) { .footer-nav { gap: 32px; } .footer-top { flex-direction: column; } }
```

---

## Dashboard Shell

```html
<div class="dashboard">
  <aside class="sidebar">
    <div class="sidebar-logo">Brand</div>
    <nav class="sidebar-nav">
      <a href="#" class="sidebar-link active">Dashboard</a>
      <a href="#" class="sidebar-link">Analytics</a>
      <a href="#" class="sidebar-link">Settings</a>
    </nav>
  </aside>
  <div class="dashboard-body">
    <header class="topbar">
      <h1 class="text-h3">Page Title</h1>
      <div class="topbar-actions"><!-- user avatar etc. --></div>
    </header>
    <main class="dashboard-main">
      <div class="grid-4 kpi-row"><!-- stat cards --></div>
      <!-- main content -->
    </main>
  </div>
</div>
```

```css
.dashboard { display: flex; min-height: 100vh; }
.sidebar { width: 240px; min-width: 240px; background: #FFFFFF; border-right: 1px solid #E2E6EA;
           padding: 24px 0; position: sticky; top: 0; height: 100vh; overflow-y: auto; }
.sidebar-logo { padding: 0 24px 24px; font-weight: 700; font-size: 1.125rem; border-bottom: 1px solid #E2E6EA; margin-bottom: 8px; }
.sidebar-link { display: flex; align-items: center; gap: 10px; padding: 10px 24px;
               color: #4A4A68; font-size: 0.9375rem; border-radius: 0; transition: all .15s; }
.sidebar-link:hover { background: #F8F9FA; color: #1A1A2E; }
.sidebar-link.active { background: #E0E7FF; color: #4F46E5; font-weight: 600; }
.dashboard-body { flex: 1; min-width: 0; display: flex; flex-direction: column; }
.topbar { padding: 20px 32px; background: white; border-bottom: 1px solid #E2E6EA;
          display: flex; align-items: center; justify-content: space-between; position: sticky; top: 0; z-index: 10; }
.dashboard-main { padding: 32px; flex: 1; background: #F8F9FA; }
@media (max-width: 1024px) { .sidebar { width: 200px; min-width: 200px; } }
@media (max-width: 768px) {
  .dashboard { flex-direction: column; }
  .sidebar { width: 100%; height: auto; position: relative; }
  .sidebar-nav { display: flex; overflow-x: auto; padding: 0 16px; }
}
```