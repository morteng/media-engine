import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  FileText,
  Shield,
  Hammer,
  BarChart3,
  Search,
  Film,
  Image,
  Sparkles
} from 'lucide-react';
import clsx from 'clsx';

const navItems = [
  { path: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { path: '/content', icon: FileText, label: 'Content' },
  { path: '/video', icon: Film, label: 'Video' },
  { path: '/media', icon: Image, label: 'Media' },
  { path: '/quality', icon: Shield, label: 'Quality' },
  { path: '/build', icon: Hammer, label: 'Build' },
  { path: '/insights', icon: BarChart3, label: 'Insights' },
  { path: '/ai-assist', icon: Sparkles, label: 'AI Assist' },
  { path: '/search', icon: Search, label: 'Search' },
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
            end={item.path === '/'}
          >
            <item.icon size={18} />
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
