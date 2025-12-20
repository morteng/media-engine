import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Search,
  Home,
  FileText,
  Film,
  Image,
  CheckCircle,
  Package,
  BarChart3,
  Sparkles,
  Moon,
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
    // Navigation
    { id: 'nav-home', label: 'Go to Dashboard', icon: <Home size={16} />, action: () => navigate('/'), category: 'Navigation' },
    { id: 'nav-content', label: 'Go to Content', icon: <FileText size={16} />, action: () => navigate('/content'), category: 'Navigation' },
    { id: 'nav-video', label: 'Go to Video', icon: <Film size={16} />, action: () => navigate('/video'), category: 'Navigation' },
    { id: 'nav-media', label: 'Go to Media', icon: <Image size={16} />, action: () => navigate('/media'), category: 'Navigation' },
    { id: 'nav-quality', label: 'Go to Quality', icon: <CheckCircle size={16} />, action: () => navigate('/quality'), category: 'Navigation' },
    { id: 'nav-build', label: 'Go to Build', icon: <Package size={16} />, action: () => navigate('/build'), category: 'Navigation' },
    { id: 'nav-insights', label: 'Go to Insights', icon: <BarChart3 size={16} />, action: () => navigate('/insights'), category: 'Navigation' },
    { id: 'nav-ai', label: 'Go to AI Assist', icon: <Sparkles size={16} />, action: () => navigate('/ai-assist'), category: 'Navigation' },
    { id: 'nav-search', label: 'Go to Search', icon: <Search size={16} />, action: () => navigate('/search'), category: 'Navigation' },
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
