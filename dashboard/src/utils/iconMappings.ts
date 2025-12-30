/**
 * Centralized icon mappings for consistent UI across the dashboard
 * Use these instead of defining icon maps in individual components
 */

import {
  Book,
  BookOpen,
  FileText,
  Presentation,
  Table,
  FileSpreadsheet,
  Film,
  Video,
  Image,
  Music,
  Layers,
  Database,
  CheckCircle,
  AlertCircle,
  Clock,
  XCircle,
  Info,
  AlertTriangle,
  type LucideIcon,
} from 'lucide-react';

// ============================================================================
// Publication Type Icons
// ============================================================================

export const PUBLICATION_TYPE_ICONS: Record<string, LucideIcon> = {
  book: BookOpen,
  deck: Presentation,
  spreadsheet: Table,
  report: FileSpreadsheet,
  video: Film,
  website: FileText,
  package: FileText,
};

/**
 * Get icon for a publication type
 */
export function getPublicationTypeIcon(type: string | undefined | null): LucideIcon {
  if (!type) return Book;
  return PUBLICATION_TYPE_ICONS[type.toLowerCase()] || Book;
}

// ============================================================================
// Format Icons
// ============================================================================

export const FORMAT_ICONS: Record<string, LucideIcon> = {
  html: FileText,
  pptx: Presentation,
  xlsx: Table,
  pdf: FileText,
  video: Film,
  mp4: Film,
  webm: Film,
};

/**
 * Get icon for a file format
 */
export function getFormatIcon(format: string | undefined | null): LucideIcon {
  if (!format) return FileText;
  return FORMAT_ICONS[format.toLowerCase()] || FileText;
}

// ============================================================================
// Item/Content Type Icons
// ============================================================================

export const ITEM_TYPE_ICONS: Record<string, LucideIcon> = {
  chapters: FileText,
  chapter: FileText,
  slides: Layers,
  slide: Layers,
  sources: Database,
  source: Database,
  items: FileText,
  item: FileText,
};

/**
 * Get icon for an item/content type
 */
export function getItemTypeIcon(itemType: string | undefined | null): LucideIcon {
  if (!itemType) return FileText;
  return ITEM_TYPE_ICONS[itemType.toLowerCase()] || FileText;
}

// ============================================================================
// Media Type Icons
// ============================================================================

export const MEDIA_TYPE_ICONS: Record<string, LucideIcon> = {
  video: Video,
  audio: Music,
  image: Image,
  document: FileText,
};

/**
 * Get icon for a media type
 */
export function getMediaTypeIcon(mediaType: string | undefined | null): LucideIcon {
  if (!mediaType) return FileText;
  return MEDIA_TYPE_ICONS[mediaType.toLowerCase()] || FileText;
}

// ============================================================================
// Status Icons
// ============================================================================

export const STATUS_ICONS: Record<string, LucideIcon> = {
  success: CheckCircle,
  completed: CheckCircle,
  valid: CheckCircle,
  active: CheckCircle,
  published: CheckCircle,
  approved: CheckCircle,
  warning: AlertTriangle,
  pending: Clock,
  in_progress: Clock,
  in_review: Clock,
  queued: Clock,
  outdated: AlertTriangle,
  error: XCircle,
  failed: XCircle,
  invalid: XCircle,
  info: Info,
  draft: FileText,
  archived: FileText,
};

/**
 * Get icon for a status
 */
export function getStatusIcon(status: string | undefined | null): LucideIcon {
  if (!status) return Info;
  return STATUS_ICONS[status.toLowerCase()] || Info;
}

// ============================================================================
// Toast/Notification Icons
// ============================================================================

export const TOAST_TYPE_ICONS: Record<string, LucideIcon> = {
  success: CheckCircle,
  error: AlertCircle,
  warning: AlertTriangle,
  info: Info,
};

/**
 * Get icon for a toast/notification type
 */
export function getToastIcon(type: string | undefined | null): LucideIcon {
  if (!type) return Info;
  return TOAST_TYPE_ICONS[type.toLowerCase()] || Info;
}
