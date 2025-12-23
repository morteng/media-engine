import { NavLink } from 'react-router-dom';
import { useSidebar } from '@/contexts';
import {
  LayoutDashboard,
  FileText,
  Shield,
  Hammer,
  Sparkles,
  X,
} from 'lucide-react';
import clsx from 'clsx';
import { NavTooltip } from '@/components/ui/InfoTooltip';

const navItems = [
  { path: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { path: '/content', icon: FileText, label: 'Content' },
  { path: '/quality', icon: Shield, label: 'Quality' },
  { path: '/build', icon: Hammer, label: 'Build' },
  { path: '/ai-assist', icon: Sparkles, label: 'AI Assist' },
];

export function Sidebar() {
  const { isCollapsed, isMobileOpen, isMobile, closeMobileMenu } = useSidebar();

  const handleNavClick = () => {
    // Close mobile menu on navigation
    if (isMobile && isMobileOpen) {
      closeMobileMenu();
    }
  };

  return (
    <>
      {/* Mobile overlay backdrop */}
      {isMobile && isMobileOpen && (
        <div className="sidebar-backdrop" onClick={closeMobileMenu} />
      )}

      <aside className={clsx('sidebar', {
        collapsed: isCollapsed && !isMobile,
        'mobile-open': isMobile && isMobileOpen,
        'mobile-closed': isMobile && !isMobileOpen,
      })}>
        {/* Mobile header with close button */}
        {isMobile && isMobileOpen && (
          <div className="sidebar-header">
            <span className="sidebar-title">Menu</span>
            <button className="sidebar-close" onClick={closeMobileMenu} title="Close menu">
              <X size={20} />
            </button>
          </div>
        )}

        <nav className="sidebar-nav">
          {navItems.map((item) => (
            <NavTooltip
              key={item.path}
              label={item.label}
              show={isCollapsed && !isMobile}
            >
              <NavLink
                to={item.path}
                className={({ isActive }) => clsx('nav-item', { active: isActive })}
                end={item.path === '/'}
                onClick={handleNavClick}
              >
                <item.icon size={18} />
                {(!isCollapsed || isMobile) && <span>{item.label}</span>}
              </NavLink>
            </NavTooltip>
          ))}
        </nav>
      </aside>
    </>
  );
}
