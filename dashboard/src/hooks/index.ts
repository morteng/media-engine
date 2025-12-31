// API Hooks
export { useProject, useStatus, useDocuments, useDocument, useInsights, useSaveDocument } from './useApi';
export { useApi, useFreshness, usePublicationsStatus, useAuditLog } from './useApi';
export { useHierarchyTree, useBreadcrumbs, useHierarchyNode, useFlowGraph, useUnifiedGraph } from './useApi';

// WebSocket
export { useWebSocket, type WebSocketMessage, type WebSocketState } from './useWebSocket';

// Video Production
export { useDemoRecorderData, useVideoOverviewData, useVideoAssets, useMotionComponents } from './useVideoApi';
export { useVideoProjectsData, useVideoScripts, useRenderQueue, useRenderMutation } from './useVideoApi';
export { useDemoToRemotionProps } from './useDemoToRemotionProps';

// AI
export {
  useAIConfig,
  useUpdateAIConfig,
  useAIOperations,
  useAIModels,
  useAIBackends,
  useProcessAI,
  useAITasks,
  useAITask,
  useSubmitAITask,
  useCancelAITask,
  useDeleteAITask,
  useAIQueueStats,
  aiQueryKeys,
} from './useAI';

// Utilities
export { useModal } from './useModal';
export {
  useKeyboardShortcuts,
  isMac,
  getModifierDisplay,
  type KeyboardShortcut,
  type ShortcutCallback,
  type ShortcutRegistration,
} from './useKeyboardShortcuts';
export {
  useVideoKeyboardShortcuts,
  VIDEO_SHORTCUTS,
  type VideoKeyboardShortcutsOptions,
  type VideoKeyboardShortcut,
} from './useVideoKeyboardShortcuts';
export { useUnsavedChanges, useDirtyState } from './useUnsavedChanges';
export {
  useSearch,
  createMultiFieldSearch,
  createTextSearch,
  type UseSearchOptions,
  type UseSearchResult,
} from './useSearch';
