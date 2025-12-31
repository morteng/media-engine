// Core UI Components (DaisyUI-based)
export { Card, CardHeader, CardContent, CardTitle, CardDescription, CardFooter } from './Card';
export { Badge } from './Badge';
export { Breadcrumbs, type BreadcrumbItem, type BreadcrumbsProps } from './Breadcrumbs';
export { Button } from './Button';
export { ProgressBar } from './ProgressBar';
export { Spinner, LoadingState, PageLoading } from './Spinner';

// Form Components
export { Input } from './Input';
export { Textarea } from './Textarea';
export { Select, SelectGroup, SelectValue, SelectTrigger, SelectContent, SelectLabel, SelectItem, SelectSeparator } from './Select';
export { Label } from './Label';
export { Separator } from './Separator';
export { Checkbox, CheckboxGroup } from './Checkbox';
export { Toggle, ToggleGroup } from './Toggle';
export { SearchInput, type SearchInputProps } from './SearchInput';
export { SearchHighlight, type SearchHighlightProps } from './SearchHighlight';
export { highlightText, escapeRegex } from '@/utils/searchUtils';

// Error Handling
export { ErrorBoundary, PageErrorFallback, withErrorBoundary } from './ErrorBoundary';
export { ConfirmProvider, ConfirmDialog, useConfirm } from './ConfirmDialog';
export { Modal, ConfirmModal, type ModalProps, type ConfirmModalProps } from './Modal';
export { UnsavedChangesDialog, type UnsavedChangesDialogProps } from './UnsavedChangesDialog';

// Custom Components
export { DataTable, type Column, type PaginationConfig, type SortState, type SortDirection, type DataTableProps } from './DataTable';
export { StatCard } from './StatCard';
export { SubTabs } from './SubTabs';
export { MarkdownPreview } from './MarkdownPreview';
export { MediaPlayer } from './MediaPlayer';
export { SelectionAnnotation } from './SelectionAnnotation';
export { ConnectionStatus } from './ConnectionStatus';
export { ToastProvider, useToast } from './Toast';
export { CommandPalette } from './CommandPalette';
export { Skeleton, SkeletonCard, SkeletonList, SkeletonStats, SkeletonText, SkeletonAvatar, SkeletonTable } from './Skeleton';
export {
  EmptyState,
  NoResultsState,
  NoDocumentsState,
  NoFilesState,
  NoTasksState,
  NoCommentsState,
  NoPublicationsState,
  NoDeliverablesState,
  NoSessionsState,
  NoNotesState,
  NoResearchState,
  NoDecisionsState,
  NoMediaState,
  NoScriptsState,
  NoPropsState,
  NoScenesState,
  NoComponentsState,
} from './EmptyState';
export { ErrorState, NetworkErrorState, LoadErrorState, PageErrorState } from './ErrorState';
export { ExpandableSection, AnalysisModule } from './ExpandableSection';
export { InfoTooltip, MetricLabel, NavTooltip, METRIC_EXPLANATIONS } from './InfoTooltip';
export { KeyboardShortcutsHelp } from './KeyboardShortcutsHelp';

// Accessibility
export { VisuallyHidden } from './VisuallyHidden';

// Utility
export { cn } from '@/utils/cn';
