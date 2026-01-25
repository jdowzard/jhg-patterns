/**
 * JHG Brand Configuration for JavaScript
 * John Holland Group
 *
 * Provides color constants for charts and dynamic styling.
 * Use with Plotly, Chart.js, or any JavaScript charting library.
 */

const JHG_BRAND = {
    // Primary Brand Colors
    colors: {
        red: '#E63946',
        redDark: '#C5303C',
        redLight: '#F5A3A9',
        redBg: '#FEF2F2',

        cyan: '#5BC0DE',
        cyanDark: '#3AA8C7',
        cyanLight: '#A8DFF0',
        cyanBg: '#ECFEFF',

        purple: '#8B5CF6',
        purpleDark: '#7C3AED',
        purpleLight: '#C4B5FD',
        purpleBg: '#F5F3FF',
    },

    // Neutral Colors
    gray: {
        900: '#111827',
        800: '#1F2937',
        700: '#374151',
        600: '#4B5563',
        500: '#6B7280',
        400: '#9CA3AF',
        300: '#D1D5DB',
        200: '#E5E7EB',
        100: '#F3F4F6',
        50: '#F9FAFB',
    },

    // Semantic Colors
    semantic: {
        success: '#10B981',
        successDark: '#059669',
        warning: '#F59E0B',
        warningDark: '#D97706',
        error: '#EF4444',
        errorDark: '#DC2626',
    },

    // Chart-specific color sets
    charts: {
        // Primary series colors
        primary: ['#E63946', '#5BC0DE', '#8B5CF6'],

        // Status indicators
        status: {
            met: '#5BC0DE',
            notMet: '#E63946',
            escalated: '#F59E0B',
        },

        // Multi-series data
        series: {
            series1: '#6B7280',
            series2: '#5BC0DE',
            series3: '#8B5CF6',
        },

        // Progress thresholds
        progressThresholds: {
            high: '#10B981',     // >= 80%
            medium: '#F59E0B',   // >= 50%
            low: '#E63946',      // < 50%
        },
    },
};

// Plotly default layout settings
const JHG_CHART_LAYOUT = {
    margin: { t: 20, r: 20, b: 40, l: 40 },
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
    font: {
        family: 'Inter, Segoe UI, system-ui, sans-serif',
        size: 12,
        color: JHG_BRAND.gray[700]
    }
};

const JHG_CHART_CONFIG = {
    responsive: true,
    displayModeBar: false
};

/**
 * Get progress bar color based on percentage.
 * @param {number} percentage - Value from 0-100
 * @returns {string} Hex color code
 */
function jhgGetProgressColor(percentage) {
    if (percentage >= 80) return JHG_BRAND.charts.progressThresholds.high;
    if (percentage >= 50) return JHG_BRAND.charts.progressThresholds.medium;
    return JHG_BRAND.charts.progressThresholds.low;
}

/**
 * Get Tailwind CSS config object for JHG colors.
 * @returns {object} Tailwind config extend object
 */
function jhgGetTailwindConfig() {
    return {
        theme: {
            extend: {
                colors: {
                    'jh-red': {
                        DEFAULT: JHG_BRAND.colors.red,
                        dark: JHG_BRAND.colors.redDark,
                        light: JHG_BRAND.colors.redLight,
                    },
                    'jh-cyan': {
                        DEFAULT: JHG_BRAND.colors.cyan,
                        dark: JHG_BRAND.colors.cyanDark,
                        light: JHG_BRAND.colors.cyanLight,
                    },
                    'jh-purple': {
                        DEFAULT: JHG_BRAND.colors.purple,
                        dark: JHG_BRAND.colors.purpleDark,
                        light: JHG_BRAND.colors.purpleLight,
                    },
                },
                fontFamily: {
                    'sans': ['Inter', 'Segoe UI', 'system-ui', 'sans-serif'],
                    'mono': ['JetBrains Mono', 'Consolas', 'monospace'],
                }
            }
        }
    };
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        JHG_BRAND,
        JHG_CHART_LAYOUT,
        JHG_CHART_CONFIG,
        jhgGetProgressColor,
        jhgGetTailwindConfig,
    };
}
