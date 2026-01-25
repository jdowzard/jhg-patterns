# jhg-patterns-web

JHG brand styling and web components for consistent styling across JHG applications.

## Installation

```bash
pip install jhg-patterns-web

# With Flask/Jinja2 support
pip install jhg-patterns-web[flask]
```

## Brand Colors

| Color | Hex | Usage |
|-------|-----|-------|
| **JH Red** | `#E63946` | Primary accent, CTAs, headers |
| **JH Cyan** | `#5BC0DE` | Secondary accent, links, info |
| **JH Purple** | `#8B5CF6` | Tertiary accent, highlights |

### Signature Gradient

The JHG signature gradient bar: Red (60%) → Cyan (20%) → Purple (20%)

```css
.jhg-gradient-bar {
    background: linear-gradient(90deg,
        #E63946 0%, #E63946 60%,
        #5BC0DE 60%, #5BC0DE 80%,
        #8B5CF6 80%, #8B5CF6 100%
    );
}
```

## Usage

### Python Constants

```python
from jhg_patterns.web import BRAND_COLORS, CHART_COLORS, get_tailwind_config

# Access colors
primary_red = BRAND_COLORS['red']['DEFAULT']  # #E63946

# Chart colors for Plotly/Chart.js
chart_colors = CHART_COLORS['primary']  # ['#E63946', '#5BC0DE', '#8B5CF6']
```

### Flask Integration

```python
from flask import Flask
from jhg_patterns.web.templates import init_flask_app

app = Flask(__name__)
init_flask_app(app)

# Now templates have access to:
# - {{ jhg_brand }} - Brand colors
# - {{ jhg_tailwind_config }} - Tailwind config
# - {{ jhg_css_variables }} - CSS custom properties
# - {{ jhg_gradient_bar }} - Gradient bar CSS
# - {{ jhg_fonts_url }} - Google Fonts URL
```

### Static Assets

Copy CSS/JS files to your project:

```python
from jhg_patterns.web.templates import copy_static_assets

copy_static_assets('./static')
# Creates:
#   ./static/css/jhg-brand.css
#   ./static/js/jhg-brand.js
```

### Component Helpers

```python
from jhg_patterns.web.templates import badge_classes, button_classes, card_classes

# Get Tailwind classes for components
badge = badge_classes('success')   # "inline-flex items-center ... bg-emerald-100"
button = button_classes('primary') # "inline-flex ... bg-jh-red hover:bg-jh-red-dark"
card = card_classes(hover=True)    # "bg-white border ... hover:shadow-md"
```

### Tailwind Config

Add JHG colors to Tailwind:

```html
<script src="https://cdn.tailwindcss.com"></script>
<script>
    tailwind.config = {{ jhg_tailwind_config | tojson }};
</script>
```

Then use: `bg-jh-red`, `text-jh-cyan`, `border-jh-purple`, etc.

## CSS Classes

The included CSS file provides utility classes:

### Colors
- `.text-jh-red`, `.text-jh-cyan`, `.text-jh-purple`
- `.bg-jh-red`, `.bg-jh-cyan`, `.bg-jh-purple`
- `.bg-jh-red-light`, `.bg-jh-cyan-light`, `.bg-jh-purple-light`

### Components
- `.jhg-gradient-bar` - Signature gradient
- `.jhg-badge`, `.jhg-badge-success`, `.jhg-badge-error`
- `.jhg-btn`, `.jhg-btn-primary`, `.jhg-btn-secondary`
- `.jhg-card`, `.jhg-card-hover`
- `.jhg-nav`, `.jhg-nav-link`
- `.jhg-alert`, `.jhg-alert-success`, `.jhg-alert-error`

## Typography

- **Primary font**: Inter (Google Fonts)
- **Monospace**: JetBrains Mono

```html
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
```
