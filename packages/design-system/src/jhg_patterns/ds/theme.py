"""
Theme system for JHG Design System.

Provides configurable color palettes, typography, spacing, and design tokens.
Themes can be loaded from YAML files or created programmatically.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml


@dataclass
class ColorPalette:
    """A color with its variants (dark, light, background)."""

    DEFAULT: str
    dark: str
    light: str
    bg: str

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "ColorPalette":
        """Create from dictionary."""
        return cls(
            DEFAULT=data.get("DEFAULT", data.get("default", "#000000")),
            dark=data.get("dark", "#000000"),
            light=data.get("light", "#ffffff"),
            bg=data.get("bg", "#f5f5f5"),
        )

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary."""
        return {
            "DEFAULT": self.DEFAULT,
            "dark": self.dark,
            "light": self.light,
            "bg": self.bg,
        }


@dataclass
class Typography:
    """Typography settings."""

    font_family: List[str] = field(default_factory=lambda: ["Inter", "system-ui", "sans-serif"])
    font_mono: List[str] = field(default_factory=lambda: ["JetBrains Mono", "Consolas", "monospace"])
    google_fonts_url: Optional[str] = None

    def __post_init__(self):
        if self.google_fonts_url is None:
            # Generate Google Fonts URL from font families
            fonts = []
            if "Inter" in self.font_family:
                fonts.append("family=Inter:wght@400;500;600;700")
            if "JetBrains Mono" in self.font_mono:
                fonts.append("family=JetBrains+Mono:wght@400;500")
            if fonts:
                self.google_fonts_url = f"https://fonts.googleapis.com/css2?{'&'.join(fonts)}&display=swap"


@dataclass
class Spacing:
    """Spacing scale (in pixels)."""

    unit: int = 4  # Base unit
    scale: List[int] = field(default_factory=lambda: [0, 4, 8, 12, 16, 24, 32, 48, 64, 96])


@dataclass
class Borders:
    """Border radius and width settings."""

    radius_sm: str = "0.25rem"
    radius: str = "0.5rem"
    radius_lg: str = "0.75rem"
    radius_xl: str = "1rem"
    radius_full: str = "9999px"


@dataclass
class Shadows:
    """Shadow definitions."""

    sm: str = "0 1px 2px 0 rgb(0 0 0 / 0.05)"
    DEFAULT: str = "0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)"
    md: str = "0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)"
    lg: str = "0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)"


@dataclass
class GradientStop:
    """A stop in the gradient bar."""

    color: str  # "primary", "secondary", "tertiary" or hex
    percent: int


@dataclass
class NavbarConfig:
    """Navbar configuration."""

    bg: str = "gray-700"
    height: str = "4rem"
    gradient_bar: bool = True


@dataclass
class Theme:
    """
    Complete theme configuration for JHG Design System.

    Can be created programmatically or loaded from YAML.
    """

    name: str

    # Brand colors (required)
    primary: ColorPalette
    secondary: ColorPalette
    tertiary: ColorPalette

    # Semantic colors (optional - have defaults)
    success: ColorPalette = field(default_factory=lambda: ColorPalette("#10B981", "#059669", "#6EE7B7", "#ECFDF5"))
    warning: ColorPalette = field(default_factory=lambda: ColorPalette("#F59E0B", "#D97706", "#FCD34D", "#FFFBEB"))
    error: ColorPalette = field(default_factory=lambda: ColorPalette("#EF4444", "#DC2626", "#FCA5A5", "#FEF2F2"))
    info: Optional[ColorPalette] = None  # Defaults to secondary

    # Gray scale
    gray: Dict[str, str] = field(default_factory=lambda: {
        "900": "#111827",
        "800": "#1F2937",
        "700": "#374151",
        "600": "#4B5563",
        "500": "#6B7280",
        "400": "#9CA3AF",
        "300": "#D1D5DB",
        "200": "#E5E7EB",
        "100": "#F3F4F6",
        "50": "#F9FAFB",
    })

    # Design tokens
    typography: Typography = field(default_factory=Typography)
    spacing: Spacing = field(default_factory=Spacing)
    borders: Borders = field(default_factory=Borders)
    shadows: Shadows = field(default_factory=Shadows)

    # Component config
    navbar: NavbarConfig = field(default_factory=NavbarConfig)
    gradient_stops: List[GradientStop] = field(default_factory=lambda: [
        GradientStop("primary", 60),
        GradientStop("secondary", 80),
        GradientStop("tertiary", 100),
    ])

    def __post_init__(self):
        # Default info to secondary if not set
        if self.info is None:
            self.info = ColorPalette(
                self.secondary.DEFAULT,
                self.secondary.dark,
                self.secondary.light,
                self.secondary.bg,
            )

    @classmethod
    def jhg(cls) -> "Theme":
        """John Holland Group default theme."""
        return cls(
            name="jhg",
            primary=ColorPalette("#E63946", "#C5303C", "#F5A3A9", "#FEF2F2"),
            secondary=ColorPalette("#5BC0DE", "#3AA8C7", "#A8DFF0", "#ECFEFF"),
            tertiary=ColorPalette("#8B5CF6", "#7C3AED", "#C4B5FD", "#F5F3FF"),
        )

    @classmethod
    def from_yaml(cls, path: str | Path) -> "Theme":
        """Load theme from YAML file."""
        with open(path) as f:
            data = yaml.safe_load(f)
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Theme":
        """Create theme from dictionary."""
        # Parse colors
        colors = data.get("colors", data)

        primary = ColorPalette.from_dict(colors.get("primary", {}))
        secondary = ColorPalette.from_dict(colors.get("secondary", {}))
        tertiary = ColorPalette.from_dict(colors.get("tertiary", {}))

        # Optional semantic colors
        success = ColorPalette.from_dict(colors["success"]) if "success" in colors else None
        warning = ColorPalette.from_dict(colors["warning"]) if "warning" in colors else None
        error = ColorPalette.from_dict(colors["error"]) if "error" in colors else None
        info = ColorPalette.from_dict(colors["info"]) if "info" in colors else None

        # Typography
        typography = None
        if "typography" in data:
            t = data["typography"]
            typography = Typography(
                font_family=t.get("font_family", Typography.font_family),
                font_mono=t.get("font_mono", Typography.font_mono),
            )

        # Gradient stops
        gradient_stops = None
        if "gradient" in data:
            gradient_stops = [
                GradientStop(color=g[0], percent=g[1])
                for g in data["gradient"]
            ]

        kwargs = {
            "name": data.get("name", "custom"),
            "primary": primary,
            "secondary": secondary,
            "tertiary": tertiary,
        }

        if success:
            kwargs["success"] = success
        if warning:
            kwargs["warning"] = warning
        if error:
            kwargs["error"] = error
        if info:
            kwargs["info"] = info
        if typography:
            kwargs["typography"] = typography
        if gradient_stops:
            kwargs["gradient_stops"] = gradient_stops
        if "gray" in colors:
            kwargs["gray"] = colors["gray"]

        return cls(**kwargs)

    def get_color(self, name: str) -> ColorPalette:
        """Get a color palette by name."""
        colors = {
            "primary": self.primary,
            "secondary": self.secondary,
            "tertiary": self.tertiary,
            "success": self.success,
            "warning": self.warning,
            "error": self.error,
            "info": self.info,
        }
        return colors.get(name)

    def resolve_color(self, value: str) -> str:
        """
        Resolve a color reference to a hex value.

        Args:
            value: Color name ("primary", "secondary.dark") or hex ("#E63946")

        Returns:
            Hex color value
        """
        if value.startswith("#"):
            return value

        if value.startswith("gray-"):
            shade = value.split("-")[1]
            return self.gray.get(shade, "#000000")

        parts = value.split(".")
        palette = self.get_color(parts[0])
        if palette is None:
            return "#000000"

        if len(parts) == 1:
            return palette.DEFAULT

        return getattr(palette, parts[1], palette.DEFAULT)

    def get_gradient_css(self) -> str:
        """Generate CSS for the gradient bar."""
        stops = []
        prev_percent = 0

        for stop in self.gradient_stops:
            color = self.resolve_color(stop.color)
            stops.append(f"{color} {prev_percent}%")
            stops.append(f"{color} {stop.percent}%")
            prev_percent = stop.percent

        return f"linear-gradient(90deg, {', '.join(stops)})"

    def get_css_variables(self) -> str:
        """Generate CSS custom properties."""
        lines = []

        # Brand colors
        for name, palette in [
            ("primary", self.primary),
            ("secondary", self.secondary),
            ("tertiary", self.tertiary),
        ]:
            lines.append(f"--{name}: {palette.DEFAULT};")
            lines.append(f"--{name}-dark: {palette.dark};")
            lines.append(f"--{name}-light: {palette.light};")
            lines.append(f"--{name}-bg: {palette.bg};")

        lines.append("")

        # Semantic colors
        for name, palette in [
            ("success", self.success),
            ("warning", self.warning),
            ("error", self.error),
            ("info", self.info),
        ]:
            lines.append(f"--{name}: {palette.DEFAULT};")
            lines.append(f"--{name}-dark: {palette.dark};")
            lines.append(f"--{name}-light: {palette.light};")
            lines.append(f"--{name}-bg: {palette.bg};")

        lines.append("")

        # Gray scale
        for shade, value in self.gray.items():
            lines.append(f"--gray-{shade}: {value};")

        lines.append("")

        # Shadows
        lines.append(f"--shadow-sm: {self.shadows.sm};")
        lines.append(f"--shadow: {self.shadows.DEFAULT};")
        lines.append(f"--shadow-md: {self.shadows.md};")
        lines.append(f"--shadow-lg: {self.shadows.lg};")

        lines.append("")

        # Border radius
        lines.append(f"--radius-sm: {self.borders.radius_sm};")
        lines.append(f"--radius: {self.borders.radius};")
        lines.append(f"--radius-lg: {self.borders.radius_lg};")
        lines.append(f"--radius-xl: {self.borders.radius_xl};")
        lines.append(f"--radius-full: {self.borders.radius_full};")

        return "\n".join(lines)

    def get_tailwind_config(self) -> Dict[str, Any]:
        """Generate Tailwind CSS configuration."""
        return {
            "theme": {
                "extend": {
                    "colors": {
                        "primary": {
                            "DEFAULT": self.primary.DEFAULT,
                            "dark": self.primary.dark,
                            "light": self.primary.light,
                        },
                        "secondary": {
                            "DEFAULT": self.secondary.DEFAULT,
                            "dark": self.secondary.dark,
                            "light": self.secondary.light,
                        },
                        "tertiary": {
                            "DEFAULT": self.tertiary.DEFAULT,
                            "dark": self.tertiary.dark,
                            "light": self.tertiary.light,
                        },
                    },
                    "fontFamily": {
                        "sans": self.typography.font_family,
                        "mono": self.typography.font_mono,
                    },
                }
            }
        }

    def get_chart_colors(self) -> Dict[str, Any]:
        """Get color configuration for charts (Plotly, Chart.js)."""
        return {
            "primary": [self.primary.DEFAULT, self.secondary.DEFAULT, self.tertiary.DEFAULT],
            "status": {
                "met": self.secondary.DEFAULT,
                "not_met": self.primary.DEFAULT,
                "escalated": self.warning.DEFAULT,
            },
            "series": {
                "series1": self.gray["500"],
                "series2": self.secondary.DEFAULT,
                "series3": self.tertiary.DEFAULT,
            },
            "progress": {
                "high": self.success.DEFAULT,
                "medium": self.warning.DEFAULT,
                "low": self.error.DEFAULT,
            },
        }
