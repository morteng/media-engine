/**
 * Graph Theme Configuration for Reagraph
 * Matches the "Electric Aurora" design system
 */

// Node type colors
export const nodeTypeColors = {
  dark: {
    document: '#00d4ff',    // Electric cyan
    chapter: '#00d4ff',
    concept: '#a855f7',     // Vivid purple
    orphan: '#f59e0b',      // Warning amber
    stale: '#ef4444',       // Error red
    hub: '#22c55e',         // Success green
    default: '#64748b',     // Slate
  },
  light: {
    document: '#6366f1',    // Indigo
    chapter: '#6366f1',
    concept: '#8b5cf6',     // Violet
    orphan: '#f59e0b',
    stale: '#ef4444',
    hub: '#22c55e',
    default: '#64748b',
  },
} as const;

// Edge relationship colors
export const edgeTypeColors = {
  implements: '#22c55e',    // Green
  derives_from: '#3b82f6',  // Blue
  references: '#8b5cf6',    // Purple
  prerequisite: '#f59e0b',  // Amber
  stale: '#ef4444',         // Red
  default: '#64748b',       // Slate
} as const;

// Full Reagraph theme configuration
export const graphThemes = {
  dark: {
    canvas: {
      background: '#0f172a', // Slate 900 (matches DaisyUI dark)
    },
    node: {
      fill: '#00d4ff',
      activeFill: '#a855f7',
      opacity: 1,
      selectedOpacity: 1,
      inactiveOpacity: 0.3,
      label: {
        color: '#f8fafc',
        fontSize: 12,
        activeColor: '#ffffff',
      },
    },
    lasso: {
      border: '#00d4ff',
      background: 'rgba(0, 212, 255, 0.1)',
    },
    ring: {
      fill: '#00d4ff',
      activeFill: '#a855f7',
    },
    edge: {
      fill: '#475569',
      activeFill: '#00d4ff',
      opacity: 0.6,
      selectedOpacity: 1,
      inactiveOpacity: 0.2,
      label: {
        color: '#94a3b8',
        fontSize: 10,
        activeColor: '#f8fafc',
      },
    },
    arrow: {
      fill: '#475569',
      activeFill: '#00d4ff',
    },
    cluster: {
      stroke: '#334155',
      opacity: 0.2,
      label: {
        color: '#94a3b8',
        fontSize: 14,
      },
    },
  },
  light: {
    canvas: {
      background: '#f8fafc', // Slate 50
    },
    node: {
      fill: '#6366f1',
      activeFill: '#a855f7',
      opacity: 1,
      selectedOpacity: 1,
      inactiveOpacity: 0.3,
      label: {
        color: '#1e293b',
        fontSize: 12,
        activeColor: '#0f172a',
      },
    },
    lasso: {
      border: '#6366f1',
      background: 'rgba(99, 102, 241, 0.1)',
    },
    ring: {
      fill: '#6366f1',
      activeFill: '#a855f7',
    },
    edge: {
      fill: '#cbd5e1',
      activeFill: '#6366f1',
      opacity: 0.6,
      selectedOpacity: 1,
      inactiveOpacity: 0.2,
      label: {
        color: '#64748b',
        fontSize: 10,
        activeColor: '#1e293b',
      },
    },
    arrow: {
      fill: '#cbd5e1',
      activeFill: '#6366f1',
    },
    cluster: {
      stroke: '#e2e8f0',
      opacity: 0.3,
      label: {
        color: '#64748b',
        fontSize: 14,
      },
    },
  },
} as const;

/**
 * Get node color based on type and theme
 */
export function getNodeColor(
  type: string,
  isDark: boolean,
  options?: { isStale?: boolean; isOrphan?: boolean; isHub?: boolean }
): string {
  const colors = isDark ? nodeTypeColors.dark : nodeTypeColors.light;

  // Priority: stale > orphan > hub > type
  if (options?.isStale) return colors.stale;
  if (options?.isOrphan) return colors.orphan;
  if (options?.isHub) return colors.hub;

  const normalizedType = type.toLowerCase();
  return colors[normalizedType as keyof typeof colors] ?? colors.default;
}

/**
 * Get edge color based on relationship type
 */
export function getEdgeColor(type: string, isStale?: boolean): string {
  if (isStale) return edgeTypeColors.stale;

  const normalizedType = type.toLowerCase().replace(/-/g, '_');
  return edgeTypeColors[normalizedType as keyof typeof edgeTypeColors] ?? edgeTypeColors.default;
}

/**
 * Get the appropriate theme based on isDark setting
 */
export function getGraphTheme(isDark: boolean) {
  return isDark ? graphThemes.dark : graphThemes.light;
}
