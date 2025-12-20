import { useState, useRef, useEffect } from 'react';
import { useProject, useRecentProjects, useOpenProject, useBrowseProject } from '@/hooks/useApi';
import { ConnectionStatus } from '@/components/ui';
import {
  Search,
  Moon,
  Sun,
  ChevronDown,
  FolderOpen,
  Clock,
  Check
} from 'lucide-react';

export function Header() {
  const { data: project, refetch: refetchProject } = useProject();
  const { data: recentProjects } = useRecentProjects();
  const openProject = useOpenProject();
  const browseProject = useBrowseProject();

  const [isDark, setIsDark] = useState(true);
  const [projectMenuOpen, setProjectMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  // Close menu on outside click
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setProjectMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const toggleTheme = () => {
    setIsDark(!isDark);
    document.documentElement.setAttribute('data-theme', isDark ? 'light' : 'dark');
  };

  const handleOpenProject = async (path: string) => {
    await openProject.mutateAsync(path);
    setProjectMenuOpen(false);
    refetchProject();
  };

  const handleBrowse = async () => {
    const result = await browseProject.mutateAsync();
    if (result.status === 'selected' && result.path) {
      await handleOpenProject(result.path);
    }
  };

  const currentProject = recentProjects?.current;
  const recent = recentProjects?.recent?.filter(p => p.path !== currentProject?.path) ?? [];

  return (
    <header className="header">
      {/* Project Selector */}
      <div className="project-selector" ref={menuRef}>
        <button
          className="project-button"
          onClick={() => setProjectMenuOpen(!projectMenuOpen)}
        >
          <span className="project-logo">ME</span>
          <span className="project-name">{project?.name || 'Media Engine'}</span>
          <ChevronDown size={16} className={projectMenuOpen ? 'rotate' : ''} />
        </button>

        {projectMenuOpen && (
          <div className="project-menu">
            {currentProject && (
              <div className="menu-section">
                <div className="menu-label">Current Project</div>
                <div className="menu-item current">
                  <Check size={14} />
                  <span className="item-name">{currentProject.name}</span>
                </div>
              </div>
            )}

            {recent.length > 0 && (
              <div className="menu-section">
                <div className="menu-label">Recent Projects</div>
                {recent.slice(0, 5).map((p) => (
                  <button
                    key={p.path}
                    className="menu-item"
                    onClick={() => handleOpenProject(p.path)}
                    disabled={!p.exists}
                  >
                    <Clock size={14} />
                    <span className="item-name">{p.name}</span>
                    {!p.exists && <span className="item-badge">Missing</span>}
                  </button>
                ))}
              </div>
            )}

            <div className="menu-divider" />

            <button className="menu-item" onClick={handleBrowse}>
              <FolderOpen size={14} />
              <span>Open Project...</span>
            </button>
          </div>
        )}
      </div>

      {/* Search */}
      <div className="search-container">
        <Search size={16} />
        <input
          type="text"
          placeholder="Search..."
          className="search-input"
        />
        <kbd>⌘K</kbd>
      </div>

      {/* Actions */}
      <div className="header-actions">
        <ConnectionStatus />
        <button className="icon-btn" onClick={toggleTheme} title="Toggle theme">
          {isDark ? <Sun size={18} /> : <Moon size={18} />}
        </button>
      </div>
    </header>
  );
}
