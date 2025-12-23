import { ChevronRight, Home, FileText, BookOpen, Settings, HelpCircle, Lightbulb, BookMarked } from 'lucide-react';
import clsx from 'clsx';
import type { BreadcrumbItem } from '@/api/types';

// Icons for document types
const docTypeIcons: Record<string, typeof FileText> = {
  chapter: BookOpen,
  operations: Settings,
  reference: FileText,
  tutorial: BookMarked,
  concept: Lightbulb,
  guide: HelpCircle,
};

interface BreadcrumbsProps {
  items: BreadcrumbItem[];
  onNavigate?: (path: string) => void;
  showHome?: boolean;
  className?: string;
}

export function Breadcrumbs({ items, onNavigate, showHome = true, className }: BreadcrumbsProps) {
  const handleClick = (e: React.MouseEvent, path: string) => {
    e.preventDefault();
    onNavigate?.(path);
  };

  if (!items || items.length === 0) {
    return null;
  }

  return (
    <nav className={clsx('breadcrumbs text-sm', className)} aria-label="Breadcrumb">
      <ul className="flex items-center flex-wrap gap-1">
        {/* Home link */}
        {showHome && (
          <>
            <li>
              <button
                className="btn btn-ghost btn-xs btn-square"
                onClick={(e) => handleClick(e, '')}
                title="Home"
              >
                <Home size={14} />
              </button>
            </li>
            <li className="text-base-content/30" aria-hidden="true">
              <ChevronRight size={14} />
            </li>
          </>
        )}

        {/* Breadcrumb items */}
        {items.map((item, index) => {
          const isLast = index === items.length - 1;
          const Icon = docTypeIcons[item.doc_type] || FileText;

          return (
            <li key={item.path} className="flex items-center gap-1">
              {index > 0 && (
                <span className="text-base-content/30" aria-hidden="true">
                  <ChevronRight size={14} />
                </span>
              )}

              {isLast ? (
                <span className="flex items-center gap-1.5 px-2 py-1 text-base-content" aria-current="page">
                  <Icon size={14} className="text-primary" />
                  <span className="font-medium">{item.title}</span>
                </span>
              ) : (
                <button
                  className="flex items-center gap-1.5 px-2 py-1 rounded-md text-base-content/70 hover:text-base-content hover:bg-base-300 transition-colors"
                  onClick={(e) => handleClick(e, item.path)}
                  title={item.title}
                >
                  <Icon size={14} />
                  <span>{item.title}</span>
                </button>
              )}
            </li>
          );
        })}
      </ul>
    </nav>
  );
}

export default Breadcrumbs;
