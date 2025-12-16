/**
 * ROP Design System - "Copper & Cream" Nordic Kitchen
 *
 * Warm Scandinavian minimalism meets professional kitchen precision.
 * Like a Copenhagen bistro that runs on cutting-edge AI.
 */

export const colors = {
  // Primary palette - Copper & Cream
  primary: '#2c2522',        // Warm espresso - headings
  secondary: '#4a4340',      // Warm charcoal - body text
  muted: '#8b8280',          // Warm gray - captions
  accent: '#c45c3c',         // Copper terracotta - brand accent
  accentLight: '#fdf6f3',    // Warm blush - accent backgrounds
  accentHover: '#a84832',    // Deep copper - hover states

  // Backgrounds
  bgPrimary: '#fdfbf9',      // Warm cream
  bgSecondary: '#f7f4f1',    // Light parchment
  bgTertiary: '#efe9e4',     // Warm stone
  border: '#e5ddd6',         // Soft taupe

  // Dark theme
  dark: {
    bgPrimary: '#1a1816',       // Deep warm black
    bgSecondary: '#242120',     // Warm charcoal
    bgTertiary: '#2e2a28',      // Warm dark stone
    textPrimary: '#f5f2ef',     // Warm white
    textSecondary: '#b8b2ac',   // Muted cream
    textMuted: '#7a7572',       // Warm gray
    border: '#3d3835',          // Dark taupe
    accent: '#d4775a',          // Lighter copper for dark bg
  },

  // Semantic
  success: '#2d6a4f',        // Forest green
  warning: '#b8860b',        // Warm amber
  error: '#b54a32',          // Warm red
  info: '#4a6fa5',           // Warm blue
} as const;

export const typography = {
  fonts: {
    heading: "'Fraunces', serif",
    body: "'Source Sans 3', sans-serif",
    mono: "'JetBrains Mono', monospace",
  },

  // Google Fonts import URL
  fontsUrl: "https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,100..900;1,9..144,100..900&family=JetBrains+Mono:wght@400;500;600&family=Source+Sans+3:wght@300;400;500;600;700&display=swap",

  weights: {
    light: 300,
    normal: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
    black: 900,
  },

  sizes: {
    display: 72,    // Hero headlines
    h1: 56,         // Section titles
    h2: 40,         // Subsection titles
    h3: 28,         // Feature titles
    h4: 22,         // Card titles
    body: 18,       // Body text
    small: 16,      // Captions
    xs: 14,         // Labels
  },
} as const;

export const motion = {
  duration: {
    fast: 150,      // Quick interactions
    normal: 300,    // Standard transitions
    slow: 500,      // Deliberate animations
    slower: 800,    // Emphasis animations
    slowest: 1200,  // Hero reveals
  },

  easing: {
    default: 'cubic-bezier(0.4, 0, 0.2, 1)',
    in: 'cubic-bezier(0.4, 0, 1, 1)',
    out: 'cubic-bezier(0, 0, 0.2, 1)',
    bounce: 'cubic-bezier(0.34, 1.56, 0.64, 1)',
    smooth: 'cubic-bezier(0.25, 0.1, 0.25, 1)',
  },
} as const;

// Gradients
export const gradients = {
  warmFade: 'linear-gradient(135deg, #fdfbf9 0%, #f7f4f1 100%)',
  copperGlow: 'linear-gradient(135deg, #c45c3c 0%, #a84832 100%)',
  darkWarm: 'linear-gradient(180deg, #1a1816 0%, #242120 100%)',
  darkRadial: 'radial-gradient(ellipse at center, #242120 0%, #1a1816 100%)',
  copperSubtle: 'linear-gradient(135deg, rgba(196, 92, 60, 0.1) 0%, rgba(196, 92, 60, 0.05) 100%)',
} as const;

// Video configuration
export const videoConfig = {
  width: 1920,
  height: 1080,
  fps: 30,
} as const;

// Feature icons (SVG paths for inline use)
export const icons = {
  menu: 'M3 12h18M3 6h18M3 18h18',
  ai: 'M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5',
  sync: 'M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15',
  shield: 'M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z',
  calendar: 'M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z',
  locations: 'M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z M15 11a3 3 0 11-6 0 3 3 0 016 0z',
  clock: 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z',
  check: 'M5 13l4 4L19 7',
} as const;

export default {
  colors,
  typography,
  motion,
  gradients,
  videoConfig,
  icons,
};
