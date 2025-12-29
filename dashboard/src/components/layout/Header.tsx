import { useState, useRef, useEffect } from 'react';
import { useProject, useRecentProjects, useOpenProject, useBrowseProject, useRemoveRecentProject } from '@/hooks/useApi';
import { useSidebar, useSettings } from '@/contexts';
import { ConnectionStatus } from '@/components/ui';
import { AgentActivityPanel } from '@/components/ai';
import {
  Search,
  Moon,
  Sun,
  ChevronDown,
  FolderOpen,
  Clock,
  Check,
  Menu,
  PanelLeft,
  PanelLeftClose,
  X,
} from 'lucide-react';

export function Header() {
  const { data: project, refetch: refetchProject } = useProject();
  const { data: recentProjects } = useRecentProjects();
  const openProject = useOpenProject();
  const browseProject = useBrowseProject();
  const removeRecentProject = useRemoveRecentProject();
  const { isMobile, isCollapsed, toggleMobileMenu, toggleSidebar } = useSidebar();
  const { toggleTheme, isDark } = useSettings();

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
    <header className="flex items-center justify-between h-14 pr-4 bg-base-200 border-b border-base-300 gap-4">
      {/* Left side - toggle and project selector */}
      <div className="flex items-center">
        <button
          className="btn btn-ghost btn-sm btn-square ml-[13px]"
          onClick={isMobile ? toggleMobileMenu : toggleSidebar}
          title={isMobile ? "Open menu" : (isCollapsed ? "Expand sidebar" : "Collapse sidebar")}
          aria-label={isMobile ? "Open navigation menu" : (isCollapsed ? "Expand sidebar" : "Collapse sidebar")}
          aria-expanded={isMobile ? undefined : !isCollapsed}
        >
          {isMobile ? (
            <Menu size={20} />
          ) : isCollapsed ? (
            <PanelLeft size={20} />
          ) : (
            <PanelLeftClose size={20} />
          )}
        </button>

        {/* Project Selector */}
        <div className={`dropdown ml-[35px] ${projectMenuOpen ? 'dropdown-open' : ''}`} ref={menuRef}>
          <button
            tabIndex={0}
            className="flex items-center gap-2 hover:opacity-80 transition-opacity"
            onClick={() => setProjectMenuOpen(!projectMenuOpen)}
          >
            <img
              src="/brand/logos/icon-64.png"
              alt="Capy"
              className="w-7 h-7 rounded-lg"
              onError={(e) => {
                // Fallback to text if image fails
                e.currentTarget.style.display = 'none';
                e.currentTarget.nextElementSibling?.classList.remove('hidden');
              }}
            />
            <span className="hidden items-center justify-center w-7 h-7 rounded bg-gradient-to-br from-primary to-secondary text-white text-xs font-bold">
              ME
            </span>
            <span className="max-w-[150px] truncate hidden sm:inline font-medium">{project?.name || 'Media Engine'}</span>
            <ChevronDown size={16} className={`transition-transform ${projectMenuOpen ? 'rotate-180' : ''}`} />
          </button>

          <div className="dropdown-content bg-base-200 rounded-box w-72 shadow-xl border border-base-300 mt-2 z-[100]">
              {currentProject && (
                <div className="px-3 pt-3 pb-1">
                  <span className="text-xs font-semibold uppercase tracking-wider text-base-content/50">Current Project</span>
                  <div className="flex items-center gap-2 px-3 py-2 mt-1 rounded-lg bg-primary/10 text-primary">
                    <Check size={14} />
                    <span className="flex-1 truncate">{currentProject.name}</span>
                  </div>
                </div>
              )}

              {recent.length > 0 && (
                <div className="px-3 pt-3 pb-1">
                  <span className="text-xs font-semibold uppercase tracking-wider text-base-content/50">Recent Projects</span>
                  <div className="mt-1 space-y-1">
                    {recent.slice(0, 5).map((p) => (
                      <div key={p.path} className="flex items-center gap-1 group">
                        <button
                          className="flex items-center gap-2 flex-1 px-3 py-2 rounded-lg text-sm text-base-content/70 hover:bg-base-300 hover:text-base-content transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                          onClick={() => handleOpenProject(p.path)}
                          disabled={!p.exists}
                        >
                          <Clock size={14} />
                          <span className="flex-1 truncate text-left">{p.name}</span>
                          {!p.exists && <span className="badge badge-error badge-xs">Missing</span>}
                        </button>
                        <button
                          className="p-1.5 rounded-lg text-base-content/30 hover:text-error hover:bg-error/10 transition-colors opacity-0 group-hover:opacity-100"
                          onClick={(e) => {
                            e.stopPropagation();
                            removeRecentProject.mutate(p.path);
                          }}
                          title="Remove from recent"
                          aria-label={`Remove ${p.name} from recent projects`}
                        >
                          <X size={14} aria-hidden="true" />
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="divider my-1"></div>

              <button
                className="flex items-center gap-2 w-full px-4 py-2 text-sm text-base-content/70 hover:bg-base-300 hover:text-base-content rounded-lg mx-2 mb-2 transition-colors"
                onClick={handleBrowse}
              >
                <FolderOpen size={14} />
                <span>Open Project...</span>
              </button>
            </div>
        </div>
      </div>

      {/* Search - triggers Command Palette */}
      <button
        className="flex items-center gap-2 flex-1 max-w-md px-3 py-2 bg-base-300 border border-base-content/10 rounded-lg text-base-content/50 hover:border-primary/50 transition-colors"
        onClick={() => {
          const event = new KeyboardEvent('keydown', {
            key: 'k',
            metaKey: true,
            bubbles: true,
          });
          document.dispatchEvent(event);
        }}
      >
        <Search size={16} />
        <span className="flex-1 text-left text-sm">Search...</span>
        <kbd className="kbd kbd-sm">⌘K</kbd>
      </button>

      {/* Right side actions */}
      <div className="flex items-center gap-2 flex-shrink-0">
        <AgentActivityPanel variant="compact" />
        <ConnectionStatus />
        <button
          className="btn btn-ghost btn-sm btn-square"
          onClick={toggleTheme}
          title={isDark ? "Switch to light theme" : "Switch to dark theme"}
          aria-label={isDark ? "Switch to light theme" : "Switch to dark theme"}
        >
          {isDark ? <Sun size={18} aria-hidden="true" /> : <Moon size={18} aria-hidden="true" />}
        </button>
      </div>
    </header>
  );
}
