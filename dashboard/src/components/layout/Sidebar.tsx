import { NavLink } from 'react-router-dom';
import { useSidebar } from '@/contexts';
import {
  LayoutDashboard,
  FileText,
  Shield,
  Hammer,
  Sparkles,
  Palette,
  Settings,
  X,
  Film,
} from 'lucide-react';
import clsx from 'clsx';
import { NavTooltip } from '@/components/ui/InfoTooltip';

// Streamlined navigation structure
const navSections = [
  {
    title: 'Overview',
    items: [
      { path: '/', icon: LayoutDashboard, label: 'Dashboard' },
      { path: '/build', icon: Hammer, label: 'Build & Publish' },
    ],
  },
  {
    title: 'Content',
    items: [
      { path: '/content', icon: FileText, label: 'Content' },
      { path: '/quality', icon: Shield, label: 'Quality' },
      { path: '/brand', icon: Palette, label: 'Brand' },
    ],
  },
  {
    title: 'Production',
    items: [
      { path: '/video', icon: Film, label: 'Video Production' },
    ],
  },
  {
    title: 'Tools',
    items: [
      { path: '/ai-assist', icon: Sparkles, label: 'AI Workspace' },
      { path: '/settings', icon: Settings, label: 'Settings' },
    ],
  },
];

// Flat list for mobile and simple mode
const flatNavItems = navSections.flatMap((section) => section.items);

export function Sidebar() {
  const { isCollapsed, isMobileOpen, isMobile, closeMobileMenu } = useSidebar();

  const handleNavClick = () => {
    // Close mobile menu on navigation
    if (isMobile && isMobileOpen) {
      closeMobileMenu();
    }
  };

  const renderNavItem = (item: typeof flatNavItems[0]) => (
    <NavTooltip
      key={item.path}
      label={item.label}
      show={isCollapsed && !isMobile}
    >
      <NavLink
        to={item.path}
        className={({ isActive }) =>
          clsx(
            'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
            {
              'bg-primary/20 text-primary': isActive,
              'text-base-content/70 hover:bg-base-300 hover:text-base-content': !isActive,
              'justify-center': isCollapsed && !isMobile,
            }
          )
        }
        end={item.path === '/'}
        onClick={handleNavClick}
      >
        <item.icon size={18} className="flex-shrink-0" />
        {(!isCollapsed || isMobile) && <span>{item.label}</span>}
      </NavLink>
    </NavTooltip>
  );

  return (
    <>
      {/* Mobile overlay backdrop */}
      {isMobile && isMobileOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={closeMobileMenu}
        />
      )}

      <aside
        className={clsx(
          'bg-base-200 border-r border-base-300 flex flex-col transition-all duration-200',
          {
            // Desktop states
            'w-48': !isCollapsed && !isMobile,
            'w-14': isCollapsed && !isMobile,
            // Mobile states
            'fixed inset-y-0 left-0 z-50 w-64 translate-x-0': isMobile && isMobileOpen,
            'fixed inset-y-0 left-0 z-50 w-64 -translate-x-full': isMobile && !isMobileOpen,
          }
        )}
      >
        {/* Mobile header with close button */}
        {isMobile && isMobileOpen && (
          <div className="flex items-center justify-between h-14 px-4 border-b border-base-300">
            <span className="font-semibold">Menu</span>
            <button
              className="btn btn-ghost btn-sm btn-square"
              onClick={closeMobileMenu}
              title="Close menu"
            >
              <X size={20} />
            </button>
          </div>
        )}

        <nav className="flex-1 p-2 overflow-y-auto">
          {isCollapsed && !isMobile ? (
            // Collapsed mode: flat list without sections
            <div className="space-y-1">
              {flatNavItems.map(renderNavItem)}
            </div>
          ) : (
            // Expanded mode: grouped by section
            <div className="space-y-4">
              {navSections.map((section) => (
                <div key={section.title}>
                  <h3 className="px-3 mb-1 text-xs font-semibold text-base-content/50 uppercase tracking-wider">
                    {section.title}
                  </h3>
                  <div className="space-y-1">
                    {section.items.map(renderNavItem)}
                  </div>
                </div>
              ))}
            </div>
          )}
        </nav>
      </aside>
    </>
  );
}
