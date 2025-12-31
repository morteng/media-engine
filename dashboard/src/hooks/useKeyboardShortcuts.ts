import { useEffect, useCallback, useState, useRef } from 'react';

export interface KeyboardShortcut {
  key: string;
  description: string;
  category: string;
  modifier?: 'cmd' | 'ctrl' | 'alt' | 'shift' | 'cmd+shift' | 'ctrl+shift';
  action?: () => void;
}

/**
 * Detects if the user is on macOS
 */
export function isMac(): boolean {
  return typeof navigator !== 'undefined' && /Mac|iPod|iPhone|iPad/.test(navigator.platform);
}

/**
 * Gets the modifier key display string based on platform
 */
export function getModifierDisplay(modifier?: string): string {
  if (!modifier) return '';
  const mac = isMac();
  const modMap: Record<string, string> = {
    cmd: mac ? '\u2318' : 'Ctrl',
    ctrl: 'Ctrl',
    alt: mac ? '\u2325' : 'Alt',
    shift: '\u21E7',
    'cmd+shift': mac ? '\u2318\u21E7' : 'Ctrl+Shift',
    'ctrl+shift': 'Ctrl+Shift',
  };
  return modMap[modifier] || modifier;
}

const DEFAULT_SHORTCUTS: KeyboardShortcut[] = [
  // Navigation
  { key: '/', description: 'Focus search / Open command palette', category: 'Navigation' },
  { key: 'K', modifier: 'cmd', description: 'Open command palette', category: 'Navigation' },
  { key: 'g h', description: 'Go to Dashboard', category: 'Navigation' },
  { key: 'g c', description: 'Go to Content', category: 'Navigation' },
  { key: 'g q', description: 'Go to Quality', category: 'Navigation' },
  { key: 'g b', description: 'Go to Build', category: 'Navigation' },
  { key: 'g a', description: 'Go to AI Workspace', category: 'Navigation' },
  { key: 'g s', description: 'Go to Settings', category: 'Navigation' },
  { key: 'g v', description: 'Go to Video Production', category: 'Navigation' },

  // Actions
  { key: 'S', modifier: 'cmd', description: 'Save current document', category: 'Actions' },
  { key: 'R', modifier: 'cmd+shift', description: 'Quick render (video pages)', category: 'Actions' },
  { key: 'Esc', description: 'Close modal / Cancel', category: 'Actions' },
  { key: '?', description: 'Show keyboard shortcuts', category: 'Help' },
];

/**
 * Type for shortcut callback registration
 */
export type ShortcutCallback = () => void;

/**
 * Interface for registering component-specific shortcuts
 */
export interface ShortcutRegistration {
  id: string;
  key: string;
  modifiers?: {
    cmd?: boolean;
    ctrl?: boolean;
    shift?: boolean;
    alt?: boolean;
  };
  callback: ShortcutCallback;
  description?: string;
  category?: string;
}

interface UseKeyboardShortcutsOptions {
  onSearch?: () => void;
  onSave?: () => void;
  onQuickRender?: () => void;
  onEscape?: () => void;
  onShowHelp?: () => void;
  onNavigate?: (path: string) => void;
  enabled?: boolean;
}

/**
 * Global keyboard shortcuts handler.
 * Provides common shortcuts for navigation and actions.
 * Supports registration of component-specific shortcuts.
 */
export function useKeyboardShortcuts({
  onSearch,
  onSave,
  onQuickRender,
  onEscape,
  onShowHelp,
  onNavigate,
  enabled = true,
}: UseKeyboardShortcutsOptions = {}) {
  const [showHelp, setShowHelp] = useState(false);
  const [pendingGoto, setPendingGoto] = useState(false);
  const registeredShortcuts = useRef<Map<string, ShortcutRegistration>>(new Map());

  /**
   * Register a component-specific shortcut.
   * Returns a cleanup function to unregister.
   */
  const registerShortcut = useCallback((registration: ShortcutRegistration) => {
    registeredShortcuts.current.set(registration.id, registration);
    return () => {
      registeredShortcuts.current.delete(registration.id);
    };
  }, []);

  /**
   * Unregister a shortcut by ID.
   */
  const unregisterShortcut = useCallback((id: string) => {
    registeredShortcuts.current.delete(id);
  }, []);

  /**
   * Get all currently registered shortcuts (for display in help).
   */
  const getRegisteredShortcuts = useCallback((): KeyboardShortcut[] => {
    const result: KeyboardShortcut[] = [];
    registeredShortcuts.current.forEach((reg) => {
      if (reg.description) {
        let modifier: KeyboardShortcut['modifier'] | undefined;
        if (reg.modifiers) {
          if (reg.modifiers.cmd && reg.modifiers.shift) modifier = 'cmd+shift';
          else if (reg.modifiers.ctrl && reg.modifiers.shift) modifier = 'ctrl+shift';
          else if (reg.modifiers.cmd) modifier = 'cmd';
          else if (reg.modifiers.ctrl) modifier = 'ctrl';
          else if (reg.modifiers.shift) modifier = 'shift';
          else if (reg.modifiers.alt) modifier = 'alt';
        }
        result.push({
          key: reg.key,
          description: reg.description,
          category: reg.category || 'Custom',
          modifier,
        });
      }
    });
    return result;
  }, []);

  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      if (!enabled) return;

      // Ignore if user is typing in an input or textarea
      const target = event.target as HTMLElement;
      const isInputActive =
        target.tagName === 'INPUT' ||
        target.tagName === 'TEXTAREA' ||
        target.isContentEditable;

      // Handle Escape (always active - for closing modals)
      if (event.key === 'Escape') {
        if (onEscape) {
          event.preventDefault();
          onEscape();
          return;
        }
        // Also close help dialog if open
        if (showHelp) {
          setShowHelp(false);
          return;
        }
      }

      // Handle Cmd+K (always active, even in inputs)
      if ((event.metaKey || event.ctrlKey) && event.key === 'k') {
        // Let CommandPalette handle this
        return;
      }

      // Handle Cmd+S (always active)
      if ((event.metaKey || event.ctrlKey) && event.key === 's' && !event.shiftKey) {
        event.preventDefault();
        onSave?.();
        return;
      }

      // Handle Cmd+Shift+R for quick render (always active)
      if ((event.metaKey || event.ctrlKey) && event.shiftKey && event.key === 'r') {
        event.preventDefault();
        onQuickRender?.();
        return;
      }

      // Check registered shortcuts (check even in inputs if they specify)
      for (const [, reg] of registeredShortcuts.current) {
        const keyMatch = event.key.toLowerCase() === reg.key.toLowerCase();
        const modMatch = !reg.modifiers || (
          (reg.modifiers.cmd === undefined || reg.modifiers.cmd === (event.metaKey || event.ctrlKey)) &&
          (reg.modifiers.ctrl === undefined || reg.modifiers.ctrl === event.ctrlKey) &&
          (reg.modifiers.shift === undefined || reg.modifiers.shift === event.shiftKey) &&
          (reg.modifiers.alt === undefined || reg.modifiers.alt === event.altKey)
        );

        if (keyMatch && modMatch) {
          event.preventDefault();
          reg.callback();
          return;
        }
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
    [enabled, onSearch, onSave, onQuickRender, onEscape, onShowHelp, onNavigate, pendingGoto, showHelp]
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
    registerShortcut,
    unregisterShortcut,
    getRegisteredShortcuts,
  };
}

export default useKeyboardShortcuts;
