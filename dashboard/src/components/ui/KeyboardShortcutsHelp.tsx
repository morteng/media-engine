import { X, Keyboard } from 'lucide-react';
import { useEffect } from 'react';

interface KeyboardShortcut {
  key: string;
  description: string;
  category: string;
  modifier?: 'cmd' | 'ctrl' | 'alt' | 'shift';
}

interface KeyboardShortcutsHelpProps {
  open: boolean;
  onClose: () => void;
  shortcuts?: KeyboardShortcut[];
}

const DEFAULT_SHORTCUTS: KeyboardShortcut[] = [
  // Navigation
  { key: '/', description: 'Focus search / Open command palette', category: 'Navigation' },
  { key: '⌘ K', description: 'Open command palette', category: 'Navigation' },
  { key: 'g h', description: 'Go to Dashboard', category: 'Navigation' },
  { key: 'g c', description: 'Go to Content', category: 'Navigation' },
  { key: 'g q', description: 'Go to Quality', category: 'Navigation' },
  { key: 'g b', description: 'Go to Build', category: 'Navigation' },
  { key: 'g a', description: 'Go to AI Workspace', category: 'Navigation' },
  { key: 'g s', description: 'Go to Settings', category: 'Navigation' },
  { key: 'g v', description: 'Go to Video Production', category: 'Navigation' },

  // Actions
  { key: '⌘ S', description: 'Save current document', category: 'Actions' },
  { key: 'Esc', description: 'Close modal / Cancel', category: 'Actions' },

  // Help
  { key: '?', description: 'Show this help', category: 'Help' },
];

/**
 * Keyboard shortcuts help dialog.
 * Shows available keyboard shortcuts organized by category.
 */
export function KeyboardShortcutsHelp({
  open,
  onClose,
  shortcuts = DEFAULT_SHORTCUTS,
}: KeyboardShortcutsHelpProps) {
  // Close on Escape
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && open) {
        onClose();
      }
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [open, onClose]);

  if (!open) return null;

  // Group shortcuts by category
  const categories = [...new Set(shortcuts.map((s) => s.category))];

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Dialog */}
      <div
        className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-lg bg-base-200 rounded-xl shadow-2xl border border-base-300 z-50 overflow-hidden"
        role="dialog"
        aria-modal="true"
        aria-labelledby="shortcuts-title"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-base-300">
          <div className="flex items-center gap-3">
            <Keyboard size={20} className="text-primary" aria-hidden="true" />
            <h2 id="shortcuts-title" className="text-lg font-semibold">
              Keyboard Shortcuts
            </h2>
          </div>
          <button
            onClick={onClose}
            className="btn btn-ghost btn-sm btn-square"
            aria-label="Close shortcuts help"
          >
            <X size={18} aria-hidden="true" />
          </button>
        </div>

        {/* Content */}
        <div className="px-6 py-4 max-h-96 overflow-y-auto">
          {categories.map((category) => (
            <div key={category} className="mb-6 last:mb-0">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-base-content/50 mb-3">
                {category}
              </h3>
              <div className="space-y-2">
                {shortcuts
                  .filter((s) => s.category === category)
                  .map((shortcut) => (
                    <div
                      key={shortcut.key}
                      className="flex items-center justify-between py-1"
                    >
                      <span className="text-sm text-base-content/80">
                        {shortcut.description}
                      </span>
                      <div className="flex items-center gap-1">
                        {shortcut.key.split(' ').map((k, i) => (
                          <kbd
                            key={i}
                            className="kbd kbd-sm min-w-[2rem] text-center"
                          >
                            {k}
                          </kbd>
                        ))}
                      </div>
                    </div>
                  ))}
              </div>
            </div>
          ))}
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-base-300 text-center text-xs text-base-content/50">
          Press <kbd className="kbd kbd-xs">?</kbd> anytime to show this help
        </div>
      </div>
    </>
  );
}

export default KeyboardShortcutsHelp;
