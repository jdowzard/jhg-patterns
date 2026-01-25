"""Tests for jhg-patterns-web brand module."""

import pytest
from jhg_patterns.web import (
    BRAND_COLORS,
    CHART_COLORS,
    SEMANTIC_COLORS,
    GRAY_SCALE,
    get_tailwind_config,
    get_css_variables,
)
from jhg_patterns.web.brand import get_gradient_bar_css, get_progress_color


class TestBrandColors:
    """Tests for brand color constants."""

    def test_brand_colors_have_required_keys(self):
        """Brand colors should have all required shades."""
        for color_name in ['red', 'cyan', 'purple']:
            assert color_name in BRAND_COLORS
            assert 'DEFAULT' in BRAND_COLORS[color_name]
            assert 'dark' in BRAND_COLORS[color_name]
            assert 'light' in BRAND_COLORS[color_name]

    def test_brand_colors_are_valid_hex(self):
        """All brand colors should be valid hex codes."""
        for color_name, shades in BRAND_COLORS.items():
            for shade_name, value in shades.items():
                assert value.startswith('#'), f"{color_name}.{shade_name} should be hex"
                assert len(value) == 7, f"{color_name}.{shade_name} should be #RRGGBB"

    def test_semantic_colors_have_required_keys(self):
        """Semantic colors should have all variants."""
        for color_name in ['success', 'warning', 'error', 'info']:
            assert color_name in SEMANTIC_COLORS
            assert 'DEFAULT' in SEMANTIC_COLORS[color_name]

    def test_gray_scale_has_standard_values(self):
        """Gray scale should have standard Tailwind-like values."""
        expected = ['900', '800', '700', '600', '500', '400', '300', '200', '100', '50']
        for shade in expected:
            assert shade in GRAY_SCALE


class TestTailwindConfig:
    """Tests for Tailwind CSS configuration."""

    def test_tailwind_config_structure(self):
        """Tailwind config should have correct structure."""
        config = get_tailwind_config()

        assert 'theme' in config
        assert 'extend' in config['theme']
        assert 'colors' in config['theme']['extend']
        assert 'fontFamily' in config['theme']['extend']

    def test_tailwind_config_has_jh_colors(self):
        """Tailwind config should include JH color prefixes."""
        config = get_tailwind_config()
        colors = config['theme']['extend']['colors']

        assert 'jh-red' in colors
        assert 'jh-cyan' in colors
        assert 'jh-purple' in colors


class TestCSSVariables:
    """Tests for CSS variable generation."""

    def test_css_variables_output(self):
        """CSS variables should be valid CSS."""
        css = get_css_variables()

        assert '--jh-red:' in css
        assert '--jh-cyan:' in css
        assert '--jh-purple:' in css
        assert '--gray-900:' in css
        assert '--success:' in css


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_gradient_bar_css(self):
        """Gradient bar should include all brand colors."""
        css = get_gradient_bar_css()

        assert 'linear-gradient' in css
        assert BRAND_COLORS['red']['DEFAULT'] in css
        assert BRAND_COLORS['cyan']['DEFAULT'] in css
        assert BRAND_COLORS['purple']['DEFAULT'] in css

    def test_progress_color_high(self):
        """High progress should return success color."""
        color = get_progress_color(80)
        assert color == CHART_COLORS['progress_thresholds']['high']

        color = get_progress_color(100)
        assert color == CHART_COLORS['progress_thresholds']['high']

    def test_progress_color_medium(self):
        """Medium progress should return warning color."""
        color = get_progress_color(50)
        assert color == CHART_COLORS['progress_thresholds']['medium']

        color = get_progress_color(79)
        assert color == CHART_COLORS['progress_thresholds']['medium']

    def test_progress_color_low(self):
        """Low progress should return error color."""
        color = get_progress_color(0)
        assert color == CHART_COLORS['progress_thresholds']['low']

        color = get_progress_color(49)
        assert color == CHART_COLORS['progress_thresholds']['low']
