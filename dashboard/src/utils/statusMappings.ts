/**
 * Centralized status/color mappings for consistent UI across the dashboard
 * Use these instead of defining status maps in individual components
 */

// ============================================================================
// Badge Variants (DaisyUI classes)
// ============================================================================

export type BadgeVariant =
  | 'default'
  | 'primary'
  | 'secondary'
  | 'accent'
  | 'success'
  | 'warning'
  | 'error'
  | 'info'
  | 'ghost'
  | 'outline';

export const BADGE_CLASSES: Record<BadgeVariant, string> = {
  default: 'badge',
  primary: 'badge badge-primary',
  secondary: 'badge badge-secondary',
  accent: 'badge badge-accent',
  success: 'badge badge-success',
  warning: 'badge badge-warning',
  error: 'badge badge-error',
  info: 'badge badge-info',
  ghost: 'badge badge-ghost',
  outline: 'badge badge-outline',
};

// ============================================================================
// Publication Status Mappings
// ============================================================================

export const PUBLICATION_STATUS_BADGES: Record<string, BadgeVariant> = {
  draft: 'warning',
  in_review: 'info',
  approved: 'primary',
  published: 'success',
  archived: 'ghost',
};

/**
 * Get badge class for a publication status
 */
export function getPublicationStatusBadge(status: string): string {
  const variant = PUBLICATION_STATUS_BADGES[status.toLowerCase()] || 'ghost';
  return BADGE_CLASSES[variant];
}

// ============================================================================
// Format Color Mappings
// ============================================================================

export const FORMAT_BADGE_VARIANTS: Record<string, BadgeVariant> = {
  html: 'info',
  pptx: 'warning',
  xlsx: 'success',
  pdf: 'error',
  video: 'secondary',
  mp4: 'secondary',
  webm: 'secondary',
};

export const FORMAT_COLORS: Record<string, { active: string; inactive: string }> = {
  html: { active: 'badge-info', inactive: 'badge-outline opacity-50' },
  pptx: { active: 'badge-warning', inactive: 'badge-outline opacity-50' },
  xlsx: { active: 'badge-success', inactive: 'badge-outline opacity-50' },
  pdf: { active: 'badge-error', inactive: 'badge-outline opacity-50' },
  mp4: { active: 'badge-secondary', inactive: 'badge-outline opacity-50' },
  video: { active: 'badge-secondary', inactive: 'badge-outline opacity-50' },
  webm: { active: 'badge-secondary', inactive: 'badge-outline opacity-50' },
};

/**
 * Get badge class for a format
 */
export function getFormatBadge(format: string, active = true): string {
  const colors = FORMAT_COLORS[format.toLowerCase()];
  if (!colors) return active ? 'badge-ghost' : 'badge-outline opacity-50';
  return active ? colors.active : colors.inactive;
}

// ============================================================================
// Format Labels
// ============================================================================

export const FORMAT_LABELS: Record<string, string> = {
  html: 'HTML',
  pptx: 'PPTX',
  xlsx: 'XLSX',
  pdf: 'PDF',
  mp4: 'MP4',
  video: 'Video',
  webm: 'WebM',
};

/**
 * Get display label for a format
 */
export function getFormatLabel(format: string): string {
  return FORMAT_LABELS[format.toLowerCase()] || format.toUpperCase();
}

// ============================================================================
// General Status Mappings
// ============================================================================

export const STATUS_BADGE_VARIANTS: Record<string, BadgeVariant> = {
  // Success states
  success: 'success',
  completed: 'success',
  valid: 'success',
  active: 'success',
  published: 'success',
  approved: 'success',
  synced: 'success',
  current: 'success',

  // Warning states
  warning: 'warning',
  pending: 'warning',
  outdated: 'warning',
  stale: 'warning',
  needs_update: 'warning',

  // Error states
  error: 'error',
  failed: 'error',
  invalid: 'error',

  // Info states
  info: 'info',
  queued: 'info',
  in_review: 'info',
  in_progress: 'info',

  // Neutral states
  draft: 'ghost',
  archived: 'ghost',
  default: 'ghost',
};

/**
 * Get badge class for any status string
 */
export function getStatusBadgeClass(status: string): string {
  const normalized = status.toLowerCase().replace(/\s+/g, '_');
  const variant = STATUS_BADGE_VARIANTS[normalized] || 'ghost';
  return BADGE_CLASSES[variant];
}

/**
 * Get badge variant for any status string
 */
export function getStatusBadgeVariant(status: string): BadgeVariant {
  const normalized = status.toLowerCase().replace(/\s+/g, '_');
  return STATUS_BADGE_VARIANTS[normalized] || 'ghost';
}

// ============================================================================
// Text Color Classes
// ============================================================================

export const STATUS_TEXT_COLORS: Record<string, string> = {
  success: 'text-success',
  completed: 'text-success',
  valid: 'text-success',
  active: 'text-success',

  warning: 'text-warning',
  pending: 'text-warning',
  outdated: 'text-warning',

  error: 'text-error',
  failed: 'text-error',
  invalid: 'text-error',

  info: 'text-info',
  queued: 'text-info',
  in_progress: 'text-info',

  muted: 'text-base-content/60',
  default: 'text-base-content/60',
};

/**
 * Get text color class for a status
 */
export function getStatusTextColor(status: string): string {
  const normalized = status.toLowerCase().replace(/\s+/g, '_');
  return STATUS_TEXT_COLORS[normalized] || 'text-base-content/60';
}

// ============================================================================
// Build Status Mappings
// ============================================================================

export const BUILD_STATUS_BADGES: Record<string, BadgeVariant> = {
  idle: 'ghost',
  queued: 'info',
  running: 'info',
  success: 'success',
  completed: 'success',
  error: 'error',
  failed: 'error',
  cancelled: 'warning',
};

/**
 * Get badge class for a build status
 */
export function getBuildStatusBadge(status: string): string {
  const variant = BUILD_STATUS_BADGES[status.toLowerCase()] || 'ghost';
  return BADGE_CLASSES[variant];
}

// ============================================================================
// AI/Task Status Mappings
// ============================================================================

export const AI_STATUS_BADGES: Record<string, BadgeVariant> = {
  pending: 'warning',
  in_progress: 'info',
  active: 'success',
  completed: 'success',
  failed: 'error',
  cancelled: 'ghost',
};

/**
 * Get badge class for an AI/task status
 */
export function getAIStatusBadge(status: string): string {
  const variant = AI_STATUS_BADGES[status.toLowerCase()] || 'ghost';
  return BADGE_CLASSES[variant];
}

// ============================================================================
// Validation Status Mappings
// ============================================================================

export const VALIDATION_STATUS: Record<string, { badge: BadgeVariant; text: string }> = {
  valid: { badge: 'success', text: 'Valid' },
  invalid: { badge: 'error', text: 'Invalid' },
  warning: { badge: 'warning', text: 'Warnings' },
  unchecked: { badge: 'ghost', text: 'Not checked' },
};

/**
 * Get validation status display info
 */
export function getValidationStatus(isValid: boolean | null | undefined): { badge: string; text: string } {
  if (isValid === true) {
    return { badge: BADGE_CLASSES.success, text: 'Valid' };
  }
  if (isValid === false) {
    return { badge: BADGE_CLASSES.error, text: 'Invalid' };
  }
  return { badge: BADGE_CLASSES.ghost, text: 'Not checked' };
}

// ============================================================================
// Video Scene Type Mappings
// ============================================================================

/** Scene type colors for timeline visualization */
export const SCENE_TYPE_COLORS: Record<string, { bg: string; border: string; text: string }> = {
  intro: { bg: 'bg-cyan-500/20', border: 'border-cyan-500', text: 'text-cyan-400' },
  content: { bg: 'bg-purple-500/20', border: 'border-purple-500', text: 'text-purple-400' },
  feature: { bg: 'bg-amber-500/20', border: 'border-amber-500', text: 'text-amber-400' },
  demo: { bg: 'bg-emerald-500/20', border: 'border-emerald-500', text: 'text-emerald-400' },
  section: { bg: 'bg-blue-500/20', border: 'border-blue-500', text: 'text-blue-400' },
  outro: { bg: 'bg-rose-500/20', border: 'border-rose-500', text: 'text-rose-400' },
  split: { bg: 'bg-indigo-500/20', border: 'border-indigo-500', text: 'text-indigo-400' },
  transition: { bg: 'bg-gray-500/20', border: 'border-gray-500', text: 'text-gray-400' },
};

/** Scene type badge variants */
export const SCENE_TYPE_BADGES: Record<string, BadgeVariant> = {
  intro: 'info',
  content: 'secondary',
  feature: 'warning',
  demo: 'success',
  section: 'primary',
  outro: 'error',
  split: 'accent',
  transition: 'ghost',
};

/**
 * Get colors for a scene type
 */
export function getSceneTypeColors(type: string): { bg: string; border: string; text: string } {
  return SCENE_TYPE_COLORS[type.toLowerCase()] || SCENE_TYPE_COLORS.content;
}

/**
 * Get badge class for a scene type
 */
export function getSceneTypeBadge(type: string): string {
  const variant = SCENE_TYPE_BADGES[type.toLowerCase()] || 'ghost';
  return BADGE_CLASSES[variant];
}

// ============================================================================
// Video Render Status Mappings
// ============================================================================

export const RENDER_STATUS_BADGES: Record<string, BadgeVariant> = {
  queued: 'info',
  rendering: 'warning',
  completed: 'success',
  failed: 'error',
  cancelled: 'ghost',
};

/**
 * Get badge class for a render status
 */
export function getRenderStatusBadge(status: string): string {
  const variant = RENDER_STATUS_BADGES[status.toLowerCase()] || 'ghost';
  return BADGE_CLASSES[variant];
}

// ============================================================================
// Video Quality Mappings
// ============================================================================

export const VIDEO_QUALITY_BADGES: Record<string, BadgeVariant> = {
  preview: 'warning',
  production: 'success',
};

/**
 * Get badge class for video quality
 */
export function getVideoQualityBadge(quality: string): string {
  const variant = VIDEO_QUALITY_BADGES[quality.toLowerCase()] || 'ghost';
  return BADGE_CLASSES[variant];
}
