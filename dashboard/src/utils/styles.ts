/**
 * Shared style constants for consistent UI patterns
 * Use these instead of repeating class strings across components
 */

// Card styles for consistent container styling
export const CARD_STYLES = {
  base: 'card bg-base-200',
  bordered: 'card bg-base-200 border border-base-300',
  elevated: 'card bg-base-200 shadow-sm hover:shadow-md transition-shadow',
  compact: 'card bg-base-200 p-3',
  interactive: 'card bg-base-200 cursor-pointer hover:bg-base-300 transition-colors',
} as const;

// Common layout patterns
export const LAYOUT = {
  flexCenter: 'flex items-center justify-center',
  flexBetween: 'flex items-center justify-between',
  flexStart: 'flex items-center gap-2',
  flexGap2: 'flex items-center gap-2',
  flexGap3: 'flex items-center gap-3',
  flexGap4: 'flex items-center gap-4',
  flexCol: 'flex flex-col',
  flexColGap2: 'flex flex-col gap-2',
  flexColGap4: 'flex flex-col gap-4',
  gridCols2: 'grid grid-cols-1 md:grid-cols-2 gap-4',
  gridCols3: 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4',
  gridCols4: 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4',
} as const;

// Standard icon sizes (matches lucide-react conventions)
export const ICON_SIZES = {
  xs: 10,
  sm: 12,
  md: 16,
  lg: 20,
  xl: 24,
  '2xl': 32,
} as const;

// Status colors for badges and indicators
export const STATUS_COLORS = {
  success: 'text-success',
  warning: 'text-warning',
  error: 'text-error',
  info: 'text-info',
  primary: 'text-primary',
  secondary: 'text-secondary',
  muted: 'text-base-content/60',
} as const;

// Badge variants (DaisyUI classes)
export const BADGE_VARIANTS = {
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
} as const;

// Button variants for consistent action styling
export const BUTTON_VARIANTS = {
  primary: 'btn btn-primary',
  secondary: 'btn btn-secondary',
  accent: 'btn btn-accent',
  ghost: 'btn btn-ghost',
  link: 'btn btn-link',
  error: 'btn btn-error',
  warning: 'btn btn-warning',
  success: 'btn btn-success',
  info: 'btn btn-info',
  outline: 'btn btn-outline',
} as const;

// Common text styles
export const TEXT_STYLES = {
  heading: 'font-bold text-lg',
  subheading: 'font-semibold text-base',
  body: 'text-sm',
  caption: 'text-xs text-base-content/60',
  muted: 'text-base-content/60',
  truncate: 'truncate',
} as const;

// Form field styles
export const FORM_STYLES = {
  input: 'input input-bordered w-full',
  inputSm: 'input input-bordered input-sm w-full',
  select: 'select select-bordered w-full',
  selectSm: 'select select-bordered select-sm w-full',
  textarea: 'textarea textarea-bordered w-full',
  label: 'label',
  labelText: 'label-text',
} as const;

// Animation classes
export const ANIMATIONS = {
  spin: 'animate-spin',
  pulse: 'animate-pulse',
  bounce: 'animate-bounce',
  fadeIn: 'animate-fade-in',
} as const;

// Spacing shortcuts
export const SPACING = {
  section: 'space-y-6',
  card: 'space-y-4',
  compact: 'space-y-2',
  list: 'space-y-1',
} as const;

// Status mapping for consistent status indicators
export const STATUS_BADGE_MAP: Record<string, keyof typeof BADGE_VARIANTS> = {
  success: 'success',
  completed: 'success',
  active: 'success',
  valid: 'success',
  warning: 'warning',
  pending: 'warning',
  outdated: 'warning',
  error: 'error',
  failed: 'error',
  invalid: 'error',
  info: 'info',
  queued: 'info',
  default: 'ghost',
};

/**
 * Get badge class for a status string
 */
export function getStatusBadgeClass(status: string): string {
  const normalizedStatus = status.toLowerCase();
  const variant = STATUS_BADGE_MAP[normalizedStatus] || 'ghost';
  return BADGE_VARIANTS[variant];
}
