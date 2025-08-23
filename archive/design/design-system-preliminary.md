# NGÜ Bibelvers-Sponsoring - Design System

Basierend auf der offiziellen NGÜ-Website (neuegenferuebersetzung.de)

## 1. Farbpalette

### Hauptfarben
- **Primärfarbe (Rot)**: `#dd3333` - Akzentfarbe für CTAs und wichtige Elemente
- **Sekundärfarbe (Dunkelgrau)**: `#323334` - Navigation und Überschriften
- **Textfarbe**: `#333333` - Haupttext
- **Textfarbe (Sekundär)**: `#666666` - Beschreibungen und Meta-Informationen
- **Hintergrund**: `#ffffff` - Haupthintergrund
- **Hintergrund (Sekundär)**: `#f5f5f5` - Abschnitte und Karten

### Zusatzfarben
- **Erfolg**: `#28a745` - Bestätigungen
- **Warnung**: `#ffc107` - Hinweise
- **Fehler**: `#dc3545` - Fehlermeldungen
- **Info**: `#17a2b8` - Informationen

## 2. Typografie

### Schriftgrößen (Responsive)
```css
--font-size-small: 15px;
--font-size-normal: 18px;
--font-size-medium: 24px;
--font-size-large: 30px;
--font-size-x-large: 42px;
--font-size-huge: 34px;
```

### Schriftarten
```css
--font-family-primary: 'Poppins', sans-serif;
--font-family-heading: 'Poppins', sans-serif;
--font-family-fallback: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
--font-family-mono: 'Courier New', Courier, monospace;
```

### Font Import
```html
<!-- Google Fonts -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap" rel="stylesheet">
```

### Überschriften-Hierarchie

- **H1**: 42px, font-weight: 700, line-height: 1.2
- **H2**: 34px, font-weight: 600, line-height: 1.3
- **H3**: 30px, font-weight: 600, line-height: 1.3
- **H4**: 24px, font-weight: 600, line-height: 1.4
- **H5**: 18px, font-weight: 600, line-height: 1.4
- **H6**: 15px, font-weight: 700, line-height: 1.4

## 3. Abstände und Layout

### Container
```css
--container-max-width: 1290px;
--container-padding: 15px;
```

### Abstände (Spacing Scale)
```css
--spacing-xs: 4px;
--spacing-sm: 8px;
--spacing-md: 16px;
--spacing-lg: 24px;
--spacing-xl: 32px;
--spacing-xxl: 48px;
--spacing-xxxl: 64px;
```

### Responsive Breakpoints
```css
--breakpoint-mobile: 767px;
--breakpoint-tablet: 991px;
--breakpoint-laptop: 1439px;
```

## 4. Komponenten-Stile

### Buttons
```css
.btn-primary {
  background-color: #dd3333;
  color: white;
  padding: 12px 24px;
  border-radius: 9999px; /* Vollständig gerundet */
  font-size: 18px;
  font-weight: 600;
  transition: all 0.3s ease;
  border: none;
  cursor: pointer;
}

.btn-primary:hover {
  background-color: #c02a2a;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0,0,0,0.15);
}

.btn-secondary {
  background-color: #323334;
  color: white;
  padding: 12px 24px;
  border-radius: 9999px;
  font-size: 18px;
  font-weight: 600;
  transition: all 0.3s ease;
}

.btn-outline {
  background-color: transparent;
  color: #dd3333;
  border: 2px solid #dd3333;
  padding: 10px 22px;
  border-radius: 9999px;
}
```

### Karten
```css
.card {
  background: white;
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  transition: box-shadow 0.3s ease;
}

.card:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}
```

### Formulare
```css
.form-input {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 16px;
  transition: border-color 0.3s ease;
}

.form-input:focus {
  outline: none;
  border-color: #dd3333;
  box-shadow: 0 0 0 3px rgba(221, 51, 51, 0.1);
}

.form-label {
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
  color: #333;
}
```

### Navigation
```css
.nav-menu {
  background-color: #323334;
  padding: 0;
}

.nav-item {
  color: white;
  padding: 16px 20px;
  transition: background-color 0.3s ease;
}

.nav-item:hover {
  background-color: #dd3333;
}
```

## 5. Animationen

### Standard-Übergänge
```css
--transition-fast: 0.2s ease;
--transition-normal: 0.3s ease;
--transition-slow: 0.5s ease;
```

### Hover-Effekte
- Buttons: translateY(-2px) und Schatten
- Karten: Verstärkter Schatten
- Links: Farbwechsel zu #dd3333

### Ladeanimation (Vers-Sponsoring)
```css
@keyframes pulse {
  0% { opacity: 1; }
  50% { opacity: 0.5; }
  100% { opacity: 1; }
}

.verse-loading {
  animation: pulse 1.5s ease-in-out infinite;
}
```

## 6. Icons und Grafiken

### Icon-Stil
- Stil: Outline/Line Icons
- Größen: 16px (small), 24px (normal), 32px (large)
- Farbe: Inherit von Parent-Element

### Bilder
- Format: WebP mit JPG/PNG Fallback
- Lazy Loading: Implementiert
- Aspect Ratios: 16:9 für Hero, 4:3 für Karten

## 7. Spezielle Elemente

### Vers-Anzeige
```css
.verse-display {
  background: #f9f9f9;
  border-left: 4px solid #dd3333;
  padding: 20px;
  margin: 20px 0;
  font-size: 18px;
  line-height: 1.6;
  font-style: italic;
}

.verse-reference {
  display: block;
  margin-top: 12px;
  font-size: 14px;
  color: #666;
  font-style: normal;
  text-align: right;
}
```

### Fortschrittsbalken
```css
.progress-bar {
  height: 8px;
  background: #e9ecef;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: #dd3333;
  transition: width 0.5s ease;
}
```

### Badge (Verfügbarkeitsstatus)
```css
.badge {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
}

.badge-available {
  background: #e8f5e9;
  color: #2e7d32;
}

.badge-sponsored {
  background: #ffebee;
  color: #c62828;
}
```

## 8. Responsive Design

### Mobile First Approach
```css
/* Base styles for mobile */
.container {
  padding: 15px;
}

/* Tablet */
@media (min-width: 768px) {
  .container {
    padding: 20px;
  }
}

/* Desktop */
@media (min-width: 992px) {
  .container {
    max-width: 1290px;
    margin: 0 auto;
  }
}
```

## 9. Accessibility

### Fokus-Stile
```css
*:focus-visible {
  outline: 2px solid #dd3333;
  outline-offset: 2px;
}
```

### Kontrast-Anforderungen
- Normaler Text: Mindestens 4.5:1
- Großer Text: Mindestens 3:1
- Interaktive Elemente: Mindestens 3:1

## 10. Dark Mode (Optional für Phase 2)

```css
@media (prefers-color-scheme: dark) {
  :root {
    --bg-primary: #1a1a1a;
    --bg-secondary: #2d2d2d;
    --text-primary: #e0e0e0;
    --text-secondary: #b0b0b0;
  }
}
```