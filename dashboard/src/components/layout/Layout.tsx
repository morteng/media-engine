import { Outlet, useNavigate } from 'react-router-dom';
import { Header } from './Header';
import { Sidebar } from './Sidebar';
import { CommandPalette, KeyboardShortcutsHelp } from '@/components/ui';
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
      <Header />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        <main className="flex-1 overflow-y-auto p-6" role="main">
          <Outlet />
        </main>
      </div>
      <CommandPalette />
      <KeyboardShortcutsHelp open={showHelp} onClose={() => setShowHelp(false)} />
    </div>
  );
}
