import { useEffect, useCallback, useState } from 'react';

export interface KeyboardShortcut {
  key: string;
  description: string;
  category: string;
  modifier?: 'cmd' | 'ctrl' | 'alt' | 'shift';
  action?: () => void;
}

const DEFAULT_SHORTCUTS: KeyboardShortcut[] = [
  // Navigation
  { key: '/', description: 'Focus search / Open command palette', category: 'Navigation' },
  { key: 'k', modifier: 'cmd', description: 'Open command palette', category: 'Navigation' },
  { key: 'g h', description: 'Go to Dashboard', category: 'Navigation' },
  { key: 'g c', description: 'Go to Content', category: 'Navigation' },
  { key: 'g q', description: 'Go to Quality', category: 'Navigation' },
  { key: 'g b', description: 'Go to Build', category: 'Navigation' },
  { key: 'g a', description: 'Go to AI Workspace', category: 'Navigation' },
  { key: 'g s', description: 'Go to Settings', category: 'Navigation' },

  // Actions
  { key: 's', modifier: 'cmd', description: 'Save current document', category: 'Actions' },
  { key: 'Escape', description: 'Close modal / Cancel', category: 'Actions' },
  { key: '?', description: 'Show keyboard shortcuts', category: 'Help' },
];

interface UseKeyboardShortcutsOptions {
  onSearch?: () => void;
  onSave?: () => void;
  onShowHelp?: () => void;
  onNavigate?: (path: string) => void;
  enabled?: boolean;
}

/**
 * Global keyboard shortcuts handler.
 * Provides common shortcuts for navigation and actions.
 */
export function useKeyboardShortcuts({
  onSearch,
  onSave,
  onShowHelp,
  onNavigate,
  enabled = true,
}: UseKeyboardShortcutsOptions = {}) {
  const [showHelp, setShowHelp] = useState(false);
  const [pendingGoto, setPendingGoto] = useState(false);

  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      if (!enabled) return;

      // Ignore if user is typing in an input or textarea
      const target = event.target as HTMLElement;
      const isInputActive =
        target.tagName === 'INPUT' ||
        target.tagName === 'TEXTAREA' ||
        target.isContentEditable;

      // Handle Cmd+K (always active, even in inputs)
      if ((event.metaKey || event.ctrlKey) && event.key === 'k') {
        // Let CommandPalette handle this
        return;
      }

      // Handle Cmd+S (always active)
      if ((event.metaKey || event.ctrlKey) && event.key === 's') {
        event.preventDefault();
        onSave?.();
        return;
      }

      // Skip other shortcuts if typing in an input
      if (isInputActive) return;

      // Handle / for search (not in inputs)
      if (event.key === '/' && !event.metaKey && !event.ctrlKey) {
        event.preventDefault();
        onSearch?.();
        return;
      }

      // Handle ? for help (shift + /)
      if (event.key === '?' || (event.shiftKey && event.key === '/')) {
        event.preventDefault();
        if (onShowHelp) {
          onShowHelp();
        } else {
          setShowHelp(true);
        }
        return;
      }

      // Handle g + key for goto navigation
      if (event.key === 'g' && !pendingGoto) {
        setPendingGoto(true);
        // Reset after 1 second if no follow-up key
        setTimeout(() => setPendingGoto(false), 1000);
        return;
      }

      // Handle goto destinations
      if (pendingGoto && onNavigate) {
        setPendingGoto(false);
        const gotoMap: Record<string, string> = {
          h: '/',           // home/dashboard
          c: '/content',    // content
          q: '/quality',    // quality
          b: '/build',      // build
          a: '/ai-assist',  // ai workspace
          s: '/settings',   // settings
          v: '/video',      // video production
        };
        const path = gotoMap[event.key];
        if (path) {
          event.preventDefault();
          onNavigate(path);
        }
      }
    },
    [enabled, onSearch, onSave, onShowHelp, onNavigate, pendingGoto]
  );

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  return {
    shortcuts: DEFAULT_SHORTCUTS,
    showHelp,
    setShowHelp,
    pendingGoto,
  };
}

export default useKeyboardShortcuts;
