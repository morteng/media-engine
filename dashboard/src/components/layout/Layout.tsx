import { Outlet, useNavigate } from 'react-router-dom';
import { Header } from './Header';
import { Sidebar } from './Sidebar';
import { CommandPalette, KeyboardShortcutsHelp, VisuallyHidden } from '@/components/ui';
import { useKeyboardShortcuts } from '@/hooks/useKeyboardShortcuts';

export function Layout() {
  const navigate = useNavigate();

  const { showHelp, setShowHelp } = useKeyboardShortcuts({
    onSearch: () => {
      // Trigger command palette via synthetic keyboard event
      const event = new KeyboardEvent('keydown', {
        key: 'k',
        metaKey: true,
        bubbles: true,
      });
      document.dispatchEvent(event);
    },
    onNavigate: (path) => navigate(path),
  });

  return (
    <div className="flex flex-col min-h-screen bg-base-100">
      {/* Skip to main content link - visible only on focus for keyboard users */}
      <VisuallyHidden focusable>
        <a
          href="#main-content"
          className="fixed top-4 left-4 z-[100] px-4 py-2 bg-primary text-primary-content font-medium rounded-lg shadow-lg focus:outline-none focus:ring-2 focus:ring-primary-focus focus:ring-offset-2"
        >
          Skip to main content
        </a>
      </VisuallyHidden>
      <Header />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        <main id="main-content" className="flex-1 overflow-y-auto p-6" role="main" tabIndex={-1}>
          <Outlet />
        </main>
      </div>
      <CommandPalette />
      <KeyboardShortcutsHelp open={showHelp} onClose={() => setShowHelp(false)} />
    </div>
  );
}
