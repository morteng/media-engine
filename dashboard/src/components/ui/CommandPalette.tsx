import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSettings } from '@/contexts';
import {
  Search,
  Home,
  FileText,
  Film,
  Image,
  Shield,
  Hammer,
  Sparkles,
  Moon,
  Sun,
  Languages,
  Clock,
  BarChart3,
  Activity,
  Palette,
  Settings,
} from 'lucide-react';

interface Command {
  id: string;
  label: string;
  shortcut?: string;
  icon: React.ReactNode;
  action: () => void;
  category: string;
}

export function CommandPalette() {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();
  const { toggleTheme, isDark } = useSettings();

  const commands: Command[] = [
    // Main Navigation
    { id: 'nav-home', label: 'Go to Dashboard', icon: <Home size={16} />, action: () => navigate('/'), category: 'Navigation' },
    { id: 'nav-content', label: 'Go to Content', icon: <FileText size={16} />, action: () => navigate('/content'), category: 'Navigation' },
    { id: 'nav-quality', label: 'Go to Quality', icon: <Shield size={16} />, action: () => navigate('/quality'), category: 'Navigation' },
    { id: 'nav-build', label: 'Go to Build', icon: <Hammer size={16} />, action: () => navigate('/build'), category: 'Navigation' },
    { id: 'nav-ai', label: 'Go to AI Assist', icon: <Sparkles size={16} />, action: () => navigate('/ai-assist'), category: 'Navigation' },
    { id: 'nav-settings', label: 'Go to Settings', icon: <Settings size={16} />, action: () => navigate('/settings'), category: 'Navigation' },

    // Content sub-pages
    { id: 'nav-documents', label: 'Content → Documents', icon: <FileText size={16} />, action: () => navigate('/content'), category: 'Content' },
    { id: 'nav-translations', label: 'Content → Translations', icon: <Languages size={16} />, action: () => navigate('/content/translations'), category: 'Content' },
    { id: 'nav-video', label: 'Content → Video', icon: <Film size={16} />, action: () => navigate('/content/video'), category: 'Content' },
    { id: 'nav-media', label: 'Content → Media', icon: <Image size={16} />, action: () => navigate('/content/media'), category: 'Content' },

    // Quality sub-pages
    { id: 'nav-quality-checks', label: 'Quality → Checks', icon: <Shield size={16} />, action: () => navigate('/quality'), category: 'Quality' },
    { id: 'nav-freshness', label: 'Quality → Freshness', icon: <Clock size={16} />, action: () => navigate('/quality/freshness'), category: 'Quality' },
    { id: 'nav-analytics', label: 'Quality → Analytics', icon: <BarChart3 size={16} />, action: () => navigate('/quality/analytics'), category: 'Quality' },
    { id: 'nav-activity', label: 'Quality → Activity', icon: <Activity size={16} />, action: () => navigate('/quality/activity'), category: 'Quality' },

    // Build sub-pages
    { id: 'nav-build-outputs', label: 'Build → Outputs', icon: <Hammer size={16} />, action: () => navigate('/build'), category: 'Build' },
    { id: 'nav-brand', label: 'Build → Brand', icon: <Palette size={16} />, action: () => navigate('/build/brand'), category: 'Build' },

    // Actions
    {
      id: 'theme-toggle',
      label: isDark ? 'Switch to Light Theme' : 'Switch to Dark Theme',
      icon: isDark ? <Sun size={16} /> : <Moon size={16} />,
      action: toggleTheme,
      category: 'Actions'
    },
  ];

  const filteredCommands = query
    ? commands.filter(cmd =>
        cmd.label.toLowerCase().includes(query.toLowerCase()) ||
        cmd.category.toLowerCase().includes(query.toLowerCase())
      )
    : commands;

  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    // Open with Cmd+K or Ctrl+K
    if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
      e.preventDefault();
      setIsOpen(prev => !prev);
    }

    if (!isOpen) return;

    // Close with Escape
    if (e.key === 'Escape') {
      setIsOpen(false);
      setQuery('');
      setSelectedIndex(0);
    }

    // Navigate with arrows
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex(prev => (prev + 1) % filteredCommands.length);
    }
    if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex(prev => (prev - 1 + filteredCommands.length) % filteredCommands.length);
    }

    // Execute with Enter
    if (e.key === 'Enter' && filteredCommands[selectedIndex]) {
      e.preventDefault();
      filteredCommands[selectedIndex].action();
      setIsOpen(false);
      setQuery('');
      setSelectedIndex(0);
    }
  }, [isOpen, filteredCommands, selectedIndex]);

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  useEffect(() => {
    setSelectedIndex(0);
  }, [query]);

  if (!isOpen) return null;

  const categories = [...new Set(filteredCommands.map(c => c.category))];

  return (
    <>
      {/* Overlay */}
      <div
        className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50"
        onClick={() => setIsOpen(false)}
      />

      {/* Modal */}
      <div className="fixed top-[20%] left-1/2 -translate-x-1/2 w-full max-w-xl bg-base-200 rounded-xl shadow-2xl border border-base-300 z-50 overflow-hidden">
        {/* Search Header */}
        <div className="flex items-center gap-3 px-4 py-3 border-b border-base-300">
          <Search size={18} className="text-base-content/50" />
          <input
            ref={inputRef}
            type="text"
            className="flex-1 bg-transparent outline-none text-base-content placeholder:text-base-content/40"
            placeholder="Type a command or search..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <kbd className="kbd kbd-sm">ESC</kbd>
        </div>

        {/* Command List */}
        <div className="max-h-80 overflow-y-auto p-2">
          {filteredCommands.length === 0 ? (
            <div className="py-8 text-center text-base-content/50">
              No commands found for "{query}"
            </div>
          ) : (
            categories.map(category => (
              <div key={category} className="mb-2">
                <div className="px-3 py-1 text-xs font-semibold uppercase tracking-wider text-base-content/50">
                  {category}
                </div>
                {filteredCommands
                  .filter(cmd => cmd.category === category)
                  .map((cmd) => {
                    const globalIdx = filteredCommands.findIndex(c => c.id === cmd.id);
                    return (
                      <button
                        key={cmd.id}
                        className={`flex items-center gap-3 w-full px-3 py-2 rounded-lg text-sm text-left transition-colors ${
                          globalIdx === selectedIndex
                            ? 'bg-primary/20 text-primary'
                            : 'text-base-content/70 hover:bg-base-300'
                        }`}
                        onClick={() => {
                          cmd.action();
                          setIsOpen(false);
                          setQuery('');
                        }}
                        onMouseEnter={() => setSelectedIndex(globalIdx)}
                      >
                        <span className="text-base-content/50">{cmd.icon}</span>
                        <span className="flex-1">{cmd.label}</span>
                        {cmd.shortcut && <kbd className="kbd kbd-xs">{cmd.shortcut}</kbd>}
                      </button>
                    );
                  })}
              </div>
            ))
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center gap-4 px-4 py-2 border-t border-base-300 text-xs text-base-content/50">
          <span><kbd className="kbd kbd-xs">↑↓</kbd> to navigate</span>
          <span><kbd className="kbd kbd-xs">↵</kbd> to select</span>
          <span><kbd className="kbd kbd-xs">esc</kbd> to close</span>
        </div>
      </div>
    </>
  );
}
