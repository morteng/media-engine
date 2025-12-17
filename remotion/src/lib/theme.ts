/**
 * Media Engine Design System - "Electric Aurora"
 *
 * Vibrant, energetic, and modern. Tech-forward visuals with
 * electric colors that pop and dynamic motion that engages.
 */

export const colors = {
  // Primary palette - Electric Aurora
  primary: '#ffffff',           // Pure white - headings
  secondary: '#e0e7ff',         // Soft lavender - body text
  muted: '#94a3b8',             // Cool gray - captions
  accent: '#00d4ff',            // Electric cyan - primary accent
  accentSecondary: '#a855f7',   // Vivid purple - secondary accent
  accentTertiary: '#22d3ee',    // Bright teal - tertiary
  accentHot: '#f43f5e',         // Hot pink/rose - highlights
  accentNeon: '#84ff57',        // Neon green - special highlights
  accentOrange: '#fb923c',      // Vibrant orange

  // Light theme backgrounds (for contrast)
  bgLight: '#f8fafc',           // Near white
  bgLightSecondary: '#f1f5f9',  // Light slate

  // Dark theme - Deep Space
  dark: {
    bgPrimary: '#030712',       // Near black with blue tint
    bgSecondary: '#0f172a',     // Deep slate
    bgTertiary: '#1e293b',      // Slate
    bgCard: '#1e1b4b',          // Deep purple card
    textPrimary: '#f8fafc',     // Near white
    textSecondary: '#cbd5e1',   // Light slate
    textMuted: '#64748b',       // Muted slate
    border: '#334155',          // Slate border
    accent: '#00d4ff',          // Electric cyan
    accentGlow: '#00d4ff33',    // Cyan glow
  },

  // Semantic - Vibrant versions
  success: '#22c55e',           // Bright green
  warning: '#f59e0b',           // Amber
  error: '#ef4444',             // Bright red
  info: '#3b82f6',              // Bright blue
} as const;

export const typography = {
  fonts: {
    heading: "'Space Grotesk', sans-serif",    // Modern geometric sans
    body: "'Inter', sans-serif",                // Clean, readable
    mono: "'JetBrains Mono', monospace",        // Technical
    display: "'Orbitron', sans-serif",          // Futuristic display
  },

  // Google Fonts import URL
  fontsUrl: "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&family=Orbitron:wght@400;500;600;700;800;900&family=Space+Grotesk:wght@300;400;500;600;700&display=swap",

  weights: {
    light: 300,
    normal: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
    black: 800,
    heavy: 900,
  },

  sizes: {
    display: 96,    // Hero headlines - bigger!
    h1: 72,         // Section titles
    h2: 56,         // Subsection titles
    h3: 40,         // Feature titles
    h4: 28,         // Card titles
    body: 20,       // Body text
    small: 18,      // Captions
    xs: 16,         // Labels
  },
} as const;

export const motion = {
  duration: {
    instant: 50,    // Micro-interactions
    fast: 100,      // Quick snaps
    quick: 200,     // Responsive feedback
    normal: 300,    // Standard transitions
    smooth: 500,    // Smooth animations
    slow: 800,      // Deliberate animations
    dramatic: 1200, // Hero reveals
    epic: 2000,     // Major transitions
  },

  easing: {
    default: 'cubic-bezier(0.4, 0, 0.2, 1)',
    in: 'cubic-bezier(0.4, 0, 1, 1)',
    out: 'cubic-bezier(0, 0, 0.2, 1)',
    inOut: 'cubic-bezier(0.4, 0, 0.2, 1)',
    bounce: 'cubic-bezier(0.34, 1.56, 0.64, 1)',
    elastic: 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',
    snap: 'cubic-bezier(0.55, 0, 0.1, 1)',
    smooth: 'cubic-bezier(0.25, 0.1, 0.25, 1)',
    power: 'cubic-bezier(0.7, 0, 0.3, 1)',
  },

  // Spring configurations for Remotion
  spring: {
    snappy: { mass: 0.5, damping: 12, stiffness: 200 },
    bouncy: { mass: 0.8, damping: 10, stiffness: 150 },
    smooth: { mass: 1, damping: 20, stiffness: 100 },
    wobbly: { mass: 1, damping: 8, stiffness: 120 },
    stiff: { mass: 0.5, damping: 15, stiffness: 300 },
    gentle: { mass: 1, damping: 25, stiffness: 80 },
  },
} as const;

// Gradients - Vibrant and dynamic
export const gradients = {
  // Hero gradients
  aurora: 'linear-gradient(135deg, #00d4ff 0%, #a855f7 50%, #f43f5e 100%)',
  auroraVertical: 'linear-gradient(180deg, #00d4ff 0%, #a855f7 50%, #f43f5e 100%)',
  auroraRadial: 'radial-gradient(ellipse at center, #a855f7 0%, #030712 70%)',

  // Electric gradients
  electricBlue: 'linear-gradient(135deg, #0ea5e9 0%, #00d4ff 100%)',
  electricPurple: 'linear-gradient(135deg, #8b5cf6 0%, #a855f7 100%)',
  electricPink: 'linear-gradient(135deg, #ec4899 0%, #f43f5e 100%)',
  electricCyan: 'linear-gradient(135deg, #22d3ee 0%, #00d4ff 100%)',

  // Neon glows
  neonCyan: 'linear-gradient(135deg, #00d4ff 0%, #22d3ee 100%)',
  neonPurple: 'linear-gradient(135deg, #a855f7 0%, #c084fc 100%)',
  neonPink: 'linear-gradient(135deg, #f43f5e 0%, #fb7185 100%)',
  neonGreen: 'linear-gradient(135deg, #22c55e 0%, #84ff57 100%)',

  // Background gradients
  darkSpace: 'linear-gradient(180deg, #030712 0%, #0f172a 100%)',
  darkPurple: 'linear-gradient(180deg, #030712 0%, #1e1b4b 50%, #030712 100%)',
  darkRadial: 'radial-gradient(ellipse at 50% 0%, #1e1b4b 0%, #030712 70%)',

  // Mesh gradients (multi-color)
  mesh: 'linear-gradient(135deg, #00d4ff22 0%, #a855f722 25%, #f43f5e22 50%, #22d3ee22 75%, #00d4ff22 100%)',

  // Text gradients (for CSS background-clip)
  textAurora: 'linear-gradient(90deg, #00d4ff, #a855f7, #f43f5e)',
  textNeon: 'linear-gradient(90deg, #84ff57, #00d4ff, #a855f7)',
} as const;

// Video configuration
export const videoConfig = {
  width: 1920,
  height: 1080,
  fps: 30,
} as const;

// Glow effects
export const glows = {
  cyan: '0 0 40px #00d4ff88, 0 0 80px #00d4ff44',
  purple: '0 0 40px #a855f788, 0 0 80px #a855f744',
  pink: '0 0 40px #f43f5e88, 0 0 80px #f43f5e44',
  neon: '0 0 20px #84ff57aa, 0 0 40px #84ff5766',
  white: '0 0 30px #ffffff66, 0 0 60px #ffffff33',
  multi: '0 0 30px #00d4ff66, 0 0 60px #a855f744, 0 0 90px #f43f5e33',
} as const;

// Feature icons (SVG paths for inline use)
export const icons = {
  // Navigation
  menu: 'M3 12h18M3 6h18M3 18h18',

  // Tech/AI
  ai: 'M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5',
  brain: 'M12 2a10 10 0 0 0-7.35 16.76A10 10 0 0 0 12 22a10 10 0 0 0 7.35-3.24A10 10 0 0 0 12 2zM8 9a1 1 0 1 1 2 0 1 1 0 0 1-2 0zm6 0a1 1 0 1 1 2 0 1 1 0 0 1-2 0zm-5 5h6m-3-2v4',
  chip: 'M9 2v2M15 2v2M9 20v2M15 20v2M2 9h2M2 15h2M20 9h2M20 15h2M6 6h12v12H6z',

  // Actions
  sync: 'M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15',
  bolt: 'M13 2L3 14h9l-1 8 10-12h-9l1-8z',
  rocket: 'M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 00-2.91-.09zM12 15l-3-3a22 22 0 012-3.95A12.88 12.88 0 0122 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 01-4 2z',
  zap: 'M13 2L3 14h9l-1 8 10-12h-9l1-8z',

  // Status
  shield: 'M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z',
  check: 'M5 13l4 4L19 7',
  checkCircle: 'M22 11.08V12a10 10 0 11-5.93-9.14M22 4L12 14.01l-3-3',

  // Time
  calendar: 'M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z',
  clock: 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z',

  // Location
  locations: 'M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z M15 11a3 3 0 11-6 0 3 3 0 016 0z',

  // Media
  play: 'M5 3l14 9-14 9V3z',
  video: 'M23 7l-7 5 7 5V7zM14 5H3a2 2 0 00-2 2v10a2 2 0 002 2h11a2 2 0 002-2V7a2 2 0 00-2-2z',

  // Code
  code: 'M16 18l6-6-6-6M8 6l-6 6 6 6',
  terminal: 'M4 17l6-6-6-6M12 19h8',

  // Data
  chart: 'M18 20V10M12 20V4M6 20v-6',
  trending: 'M23 6l-9.5 9.5-5-5L1 18',

  // Documents
  document: 'M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z M14 2v6h6',
  folder: 'M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z',
} as const;

// Particles configuration for backgrounds
export const particles = {
  count: 50,
  colors: ['#00d4ff', '#a855f7', '#f43f5e', '#22d3ee', '#84ff57'],
  sizeRange: [2, 6],
  speedRange: [0.5, 2],
  opacityRange: [0.3, 0.8],
} as const;

// Grid patterns
export const patterns = {
  dotGrid: `radial-gradient(circle, ${colors.dark.border}44 1px, transparent 1px)`,
  lineGrid: `linear-gradient(${colors.dark.border}22 1px, transparent 1px), linear-gradient(90deg, ${colors.dark.border}22 1px, transparent 1px)`,
  hexGrid: 'url("data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' width=\'28\' height=\'49\'%3E%3Cpath d=\'M14 0l14 24.5L14 49 0 24.5z\' fill=\'none\' stroke=\'%23334155\' stroke-width=\'0.5\'/%3E%3C/svg%3E")',
} as const;

export default {
  colors,
  typography,
  motion,
  gradients,
  glows,
  videoConfig,
  icons,
  particles,
  patterns,
};
