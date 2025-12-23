import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
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
  Languages,
  Clock,
  BarChart3,
  Activity,
  Palette,
} from 'lucide-react';
import './CommandPalette.css';

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

  const commands: Command[] = [
    // Main Navigation
    { id: 'nav-home', label: 'Go to Dashboard', icon: <Home size={16} />, action: () => navigate('/'), category: 'Navigation' },
    { id: 'nav-content', label: 'Go to Content', icon: <FileText size={16} />, action: () => navigate('/content'), category: 'Navigation' },
    { id: 'nav-quality', label: 'Go to Quality', icon: <Shield size={16} />, action: () => navigate('/quality'), category: 'Navigation' },
    { id: 'nav-build', label: 'Go to Build', icon: <Hammer size={16} />, action: () => navigate('/build'), category: 'Navigation' },
    { id: 'nav-ai', label: 'Go to AI Assist', icon: <Sparkles size={16} />, action: () => navigate('/ai-assist'), category: 'Navigation' },

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
      label: 'Toggle Theme',
      icon: <Moon size={16} />,
      action: () => {
        const html = document.documentElement;
        const current = html.getAttribute('data-theme');
        html.setAttribute('data-theme', current === 'light' ? 'dark' : 'light');
      },
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
      <div className="command-overlay" onClick={() => setIsOpen(false)} />
      <div className="command-palette">
        <div className="command-header">
          <Search size={18} className="command-search-icon" />
          <input
            ref={inputRef}
            type="text"
            className="command-input"
            placeholder="Type a command or search..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <kbd className="command-kbd">ESC</kbd>
        </div>
        <div className="command-list">
          {filteredCommands.length === 0 ? (
            <div className="command-empty">
              No commands found for "{query}"
            </div>
          ) : (
            categories.map(category => (
              <div key={category} className="command-group">
                <div className="command-group-label">{category}</div>
                {filteredCommands
                  .filter(cmd => cmd.category === category)
                  .map((cmd) => {
                    const globalIdx = filteredCommands.findIndex(c => c.id === cmd.id);
                    return (
                      <button
                        key={cmd.id}
                        className={`command-item ${globalIdx === selectedIndex ? 'selected' : ''}`}
                        onClick={() => {
                          cmd.action();
                          setIsOpen(false);
                          setQuery('');
                        }}
                        onMouseEnter={() => setSelectedIndex(globalIdx)}
                      >
                        <span className="command-icon">{cmd.icon}</span>
                        <span className="command-label">{cmd.label}</span>
                        {cmd.shortcut && <kbd className="command-shortcut">{cmd.shortcut}</kbd>}
                      </button>
                    );
                  })}
              </div>
            ))
          )}
        </div>
        <div className="command-footer">
          <span><kbd>↑↓</kbd> to navigate</span>
          <span><kbd>↵</kbd> to select</span>
          <span><kbd>esc</kbd> to close</span>
        </div>
      </div>
    </>
  );
}
