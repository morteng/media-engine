import { useEffect, useCallback, useRef } from 'react';
import { useBlocker } from 'react-router-dom';
import { useConfirm } from '@/components/ui';

interface UseUnsavedChangesOptions {
  /**
   * Whether there are unsaved changes
   */
  hasChanges: boolean;

  /**
   * Message to show when user tries to leave
   */
  message?: string;

  /**
   * Title for the confirmation dialog
   */
  title?: string;

  /**
   * Whether to warn on browser/tab close (beforeunload)
   */
  warnOnBrowserClose?: boolean;

  /**
   * Whether to warn on route navigation
   */
  warnOnRouteChange?: boolean;

  /**
   * Callback when user confirms leaving (discards changes)
   */
  onDiscard?: () => void;

  /**
   * Callback when user cancels leaving (stays on page)
   */
  onCancel?: () => void;
}

/**
 * Hook to warn users about unsaved changes before leaving.
 *
 * Handles both:
 * - Browser close/refresh (beforeunload event)
 * - React Router navigation (blocker API)
 *
 * @example
 * ```tsx
 * const [content, setContent] = useState(initialContent);
 * const hasChanges = content !== initialContent;
 *
 * useUnsavedChanges({
 *   hasChanges,
 *   title: 'Unsaved Changes',
 *   message: 'You have unsaved changes. Are you sure you want to leave?',
 * });
 * ```
 */
export function useUnsavedChanges({
  hasChanges,
  message = 'You have unsaved changes that will be lost if you leave this page.',
  title = 'Unsaved Changes',
  warnOnBrowserClose = true,
  warnOnRouteChange = true,
  onDiscard,
  onCancel,
}: UseUnsavedChangesOptions) {
  const { confirm } = useConfirm();
  const isConfirmingRef = useRef(false);

  // Handle browser close/refresh
  useEffect(() => {
    if (!warnOnBrowserClose || !hasChanges) return;

    const handleBeforeUnload = (event: BeforeUnloadEvent) => {
      event.preventDefault();
      // Modern browsers ignore custom messages but still show a generic prompt
      event.returnValue = message;
      return message;
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [hasChanges, message, warnOnBrowserClose]);

  // Handle React Router navigation
  const blocker = useBlocker(
    useCallback(
      () => warnOnRouteChange && hasChanges && !isConfirmingRef.current,
      [hasChanges, warnOnRouteChange]
    )
  );

  // Show confirmation dialog when blocker is triggered
  useEffect(() => {
    if (blocker.state !== 'blocked') return;

    const handleBlocked = async () => {
      isConfirmingRef.current = true;

      const confirmed = await confirm({
        title,
        description: message,
        confirmText: 'Discard Changes',
        cancelText: 'Stay',
        variant: 'warning',
      });

      isConfirmingRef.current = false;

      if (confirmed) {
        onDiscard?.();
        blocker.proceed();
      } else {
        onCancel?.();
        blocker.reset();
      }
    };

    handleBlocked();
  }, [blocker, confirm, title, message, onDiscard, onCancel]);

  return {
    /**
     * Whether there are currently unsaved changes
     */
    hasChanges,

    /**
     * Whether navigation is currently blocked
     */
    isBlocked: blocker.state === 'blocked',

    /**
     * Reset the blocker (allow navigation)
     */
    reset: () => blocker.state === 'blocked' && blocker.reset(),

    /**
     * Proceed with navigation (discard changes)
     */
    proceed: () => blocker.state === 'blocked' && blocker.proceed(),
  };
}

/**
 * Simpler hook that just tracks dirty state.
 * Use this when you need manual control over the warning flow.
 *
 * @example
 * ```tsx
 * const { isDirty, setDirty, markClean } = useDirtyState();
 *
 * const handleChange = (value) => {
 *   setContent(value);
 *   setDirty(true);
 * };
 *
 * const handleSave = async () => {
 *   await save();
 *   markClean();
 * };
 * ```
 */
export function useDirtyState(initialDirty = false) {
  const dirtyRef = useRef(initialDirty);

  const setDirty = useCallback((dirty: boolean) => {
    dirtyRef.current = dirty;
  }, []);

  const markClean = useCallback(() => {
    dirtyRef.current = false;
  }, []);

  const markDirty = useCallback(() => {
    dirtyRef.current = true;
  }, []);

  return {
    get isDirty() {
      return dirtyRef.current;
    },
    setDirty,
    markClean,
    markDirty,
  };
}

export default useUnsavedChanges;
