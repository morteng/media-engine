import * as React from 'react';
import { NavLink } from 'react-router-dom';
import { ChevronRight } from 'lucide-react';
import clsx from 'clsx';

export interface BreadcrumbItem {
  label: string;
  href?: string;
  icon?: React.ReactNode;
}

export interface BreadcrumbsProps {
  items: BreadcrumbItem[];
  separator?: React.ReactNode;
  className?: string;
}

function Breadcrumbs({ items, separator, className }: BreadcrumbsProps) {
  const defaultSeparator = <ChevronRight size={14} className="text-base-content/40" />;
  const separatorElement = separator ?? defaultSeparator;

  return (
    <nav aria-label="Breadcrumb" className={clsx('text-sm', className)}>
      <ol className="flex items-center gap-1">
        {items.map((item, index) => {
          const isLast = index === items.length - 1;

          return (
            <li key={index} className="flex items-center gap-1">
              {index > 0 && (
                <span className="mx-1" aria-hidden="true">
                  {separatorElement}
                </span>
              )}
              {isLast ? (
                <span
                  className="font-medium text-base-content flex items-center gap-1.5"
                  aria-current="page"
                >
                  {item.icon}
                  {item.label}
                </span>
              ) : item.href ? (
                <NavLink
                  to={item.href}
                  className="text-base-content/60 hover:text-base-content transition-colors flex items-center gap-1.5"
                >
                  {item.icon}
                  {item.label}
                </NavLink>
              ) : (
                <span className="text-base-content/60 flex items-center gap-1.5">
                  {item.icon}
                  {item.label}
                </span>
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}

export { Breadcrumbs };
