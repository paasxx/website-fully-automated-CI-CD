# Frontend Style Guide

## Architecture overview

```
styles/
├── main.scss         ← imports everything in the correct order
├── global/
│   ├── Variables.scss  ← Sass variables ($spacing, $font-sizes, $radii)
│   ├── Mixins.scss     ← reusable patterns (card-base, button-base, etc.)
│   └── Reset.scss      ← browser reset (currently empty)
├── components/       ← one file per component
│   ├── Dashboard/
│   │   └── Dashboard.scss
│   ├── Login/
│   │   └── Login.scss
│   ├── Navbar.scss
│   ├── Profile.scss
│   └── Spinner.scss
└── layouts/
    └── Background.scss ← CSS custom properties for theming
```

**Import order in `main.scss`:** Variables → Mixins → Reset → Components → Layouts.
This order matters: components use variables and mixins, so those must be loaded first.

---

## Sass Variables (`Variables.scss`)

These are **build-time** constants. They don't change at runtime.

```scss
// Font sizes
$base-font-size:      16px;
$heading-font-size:   20px;
$paragraph-font-size: 14px;

// Spacing scale
$space-xs: 4px;
$space-sm: 8px;
$space-md: 16px;
$space-lg: 24px;

// Border radius
$radius-sm: 5px;
$radius-lg: 20px;

// Shadows
$light-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
```

**When to use:** padding, margin, font-size, border-radius in any component.

---

## CSS Custom Properties (`Background.scss`)

These are **runtime** variables. They change when the user toggles dark/light mode. The toggle works by switching `body.dark` ↔ `body.light` className (done in `ThemeContext.jsx`).

```scss
body.light {
  --bg-color:       #e5e3de;
  --text-color:     #383830;
  --card-bg:        linear-gradient(to bottom right, #f7f5f0, #cbc9c1);
  --border-color:   #4caf50;
  --button-bg:      #4caf50cc;
  --button-bg-hover:#3b8f43;
  --button-text:    #fff;
  --input-bg:       #f0ede8;
  --navbar-bg:      linear-gradient(to right, ...);
}

body.dark {
  --bg-color:       #333;
  --text-color:     #919191;
  --card-bg:        linear-gradient(to bottom right, #2c2c2c, #000);
  --border-color:   #4caf50;
  --button-bg:      #4caf4fb6;
  --button-bg-hover:#4caf50;
  --button-text:    #ffffffc2;
  --input-bg:       #1e1e1e;
  --navbar-bg:      linear-gradient(to right, ...);
}
```

**When to use:** any color that should change between dark/light. Background, text, borders, buttons.

**Rule:** Never hardcode colors in components. Use `var(--text-color)`, `var(--bg-color)`, etc.

---

## Mixins (`Mixins.scss`)

### `@include card-base`
Standard card appearance. Use for any card-like container.
```scss
border-radius: $radius-lg;
background: var(--card-bg);
box-shadow: $light-shadow;
padding: $space-md;
border: 1px solid var(--border-color);
color: var(--text-color);
```

### `@include button-base`
Standard button appearance. Use for all buttons.
```scss
border: none;
border-radius: $radius-sm;
background-color: var(--button-bg);
color: var(--button-text);
cursor: pointer;
transition: background-color 0.3s;
```
Always add `padding` and `width` in the specific class — not in the mixin.

### `@include flex-center`
```scss
display: flex;
justify-content: center;
align-items: center;
```

### `@include card-hover`
Adds lift-on-hover animation. Use for interactive cards.

### `@include custom-scrollbar($color)`
Custom scrollbar styling for scrollable containers.

---

## Naming conventions

**BEM-inspired:**
```scss
.dashboard-card--large         // block--modifier
.dashboard-card--large__body   // block--modifier__element
.transaction-amount--credit    // block__element--modifier
```

**State classes:**
```scss
.navbar-link.active            // React Router adds this automatically
.chart-type-btn--active        // manual active state
```

---

## Component-scoped vs global styles

**Styles are global** (no CSS modules). Each component's styles are in `styles/components/<ComponentName>.scss` and imported via `main.scss`.

**Rule:** Never `import './Component.scss'` directly in a component file. This causes Vite to compile the file in isolation, without access to Variables.scss and Mixins.scss. Always add to `main.scss`.

---

## Adding new component styles

1. Create `src/styles/components/MyComponent.scss`
2. Add `@import 'components/MyComponent.scss';` in `main.scss`
3. Do NOT import the scss file directly in the JSX file

---

## Common patterns

### Form inputs
```scss
input {
    padding: $space-sm $space-md;
    border-radius: $radius-sm;
    border: 1px solid var(--border-color);
    background: var(--input-bg);
    color: var(--text-color);

    &:focus {
        border-color: var(--button-bg);
        outline: none;
    }
}
```

### Error/success messages
```scss
.some-error {
    color: #e53e3e;
    font-size: 11px;  // smaller than base, not alarming
    opacity: 0.85;
}
```

### Truncate long text
```scss
.some-element {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    min-width: 0; // required when inside a flex container
}
```

---

## Known issues / TODOs

- `@import` in Sass is deprecated (replaced by `@use`/`@forward` in Dart Sass 3). Migration to `@use` would make each file explicitly declare its dependencies. Currently works because `main.scss` loads everything in order.
- `Reset.scss` is empty — no CSS reset applied. Browser default margins/paddings may cause inconsistencies. Consider adding `box-sizing: border-box` globally.
- Variable naming is inconsistent: `$heading-font-size` vs `$base-font-size`. Consider standardizing to `$font-sm`, `$font-md`, `$font-lg`.
