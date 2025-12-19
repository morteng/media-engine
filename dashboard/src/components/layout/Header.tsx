import { useProject, useStatus } from '@/hooks/useApi';
import { Search, Bell, Settings, Moon, Sun } from 'lucide-react';
import { useState } from 'react';

export function Header() {
  const { data: project } = useProject();
  const { data: status } = useStatus();
  const [isDark, setIsDark] = useState(true);

  const toggleTheme = () => {
    setIsDark(!isDark);
    document.documentElement.setAttribute('data-theme', isDark ? 'light' : 'dark');
  };

  return (
    <header className="header">
      <div className="header-left">
        <h1 className="header-title">
          <span className="header-logo">ME</span>
          {project?.name || 'Media Engine'}
        </h1>
      </div>

      <div className="header-center">
        <div className="search-bar">
          <Search size={18} />
          <input
            type="text"
            placeholder="Search documents, media, content..."
            className="search-input"
          />
          <kbd className="search-kbd">⌘K</kbd>
        </div>
      </div>

      <div className="header-right">
        {status && (
          <div className="header-stats">
            <span className="stat">
              <span className="stat-value">{status.documentCount}</span>
              <span className="stat-label">docs</span>
            </span>
            <span className="stat">
              <span className="stat-value">{status.languageCount}</span>
              <span className="stat-label">langs</span>
            </span>
            {status.qualityIssues > 0 && (
              <span className="stat stat-warning">
                <span className="stat-value">{status.qualityIssues}</span>
                <span className="stat-label">issues</span>
              </span>
            )}
          </div>
        )}

        <button className="icon-button" onClick={toggleTheme} title="Toggle theme">
          {isDark ? <Sun size={20} /> : <Moon size={20} />}
        </button>
        <button className="icon-button" title="Notifications">
          <Bell size={20} />
        </button>
        <button className="icon-button" title="Settings">
          <Settings size={20} />
        </button>
      </div>
    </header>
  );
}
