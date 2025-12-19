import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  FileText,
  Languages,
  Lightbulb,
  Hammer,
  Shield,
  Clock,
  Activity,
  Package,
  Image,
  Search,
  GitBranch
} from 'lucide-react';
import clsx from 'clsx';

const navItems = [
  { path: '/', icon: LayoutDashboard, label: 'Overview' },
  { path: '/content', icon: FileText, label: 'Content' },
  { path: '/translations', icon: Languages, label: 'Translations' },
  { path: '/insights', icon: Lightbulb, label: 'Insights' },
  { path: '/build', icon: Hammer, label: 'Build' },
  { path: '/quality', icon: Shield, label: 'Quality' },
  { path: '/freshness', icon: Clock, label: 'Freshness' },
  { path: '/activity', icon: Activity, label: 'Activity' },
  { path: '/media', icon: Image, label: 'Media' },
  { path: '/packs', icon: Package, label: 'Packs' },
  { path: '/search', icon: Search, label: 'Search' },
  { path: '/dependencies', icon: GitBranch, label: 'Dependencies' },
];

export function Sidebar() {
  return (
    <aside className="sidebar">
      <nav className="sidebar-nav">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) => clsx('nav-item', { active: isActive })}
          >
            <item.icon size={20} />
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div className="version-badge">
          v2.0.0
        </div>
      </div>
    </aside>
  );
}
