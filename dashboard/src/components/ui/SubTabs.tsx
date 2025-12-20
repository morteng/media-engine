import { NavLink, useLocation } from 'react-router-dom';
import clsx from 'clsx';

interface Tab {
  path: string;
  label: string;
}

interface SubTabsProps {
  tabs: Tab[];
  basePath: string;
}

export function SubTabs({ tabs, basePath }: SubTabsProps) {
  const location = useLocation();

  return (
    <div className="sub-tabs">
      {tabs.map((tab) => {
        const fullPath = tab.path ? `${basePath}/${tab.path}` : basePath;
        const isActive = tab.path
          ? location.pathname.startsWith(fullPath)
          : location.pathname === basePath || location.pathname === `${basePath}/`;

        return (
          <NavLink
            key={tab.path}
            to={fullPath}
            className={clsx('sub-tab', { active: isActive })}
            end={!tab.path}
          >
            {tab.label}
          </NavLink>
        );
      })}
    </div>
  );
}
