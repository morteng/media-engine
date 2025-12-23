import { ChevronRight, Home, FileText, BookOpen, Settings, HelpCircle, Lightbulb, BookMarked } from 'lucide-react';
import clsx from 'clsx';
import type { BreadcrumbItem } from '@/api/types';
import './Breadcrumbs.css';

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
    <nav className={clsx('breadcrumbs', className)} aria-label="Breadcrumb">
      <ol className="breadcrumbs-list">
        {/* Home link */}
        {showHome && (
          <>
            <li className="breadcrumb-item">
              <button
                className="breadcrumb-link breadcrumb-home"
                onClick={(e) => handleClick(e, '')}
                title="Home"
              >
                <Home size={14} />
              </button>
            </li>
            <li className="breadcrumb-separator" aria-hidden="true">
              <ChevronRight size={14} />
            </li>
          </>
        )}

        {/* Breadcrumb items */}
        {items.map((item, index) => {
          const isLast = index === items.length - 1;
          const Icon = docTypeIcons[item.doc_type] || FileText;

          return (
            <li key={item.path} className="breadcrumb-item">
              {index > 0 && (
                <span className="breadcrumb-separator" aria-hidden="true">
                  <ChevronRight size={14} />
                </span>
              )}

              {isLast ? (
                <span className="breadcrumb-current" aria-current="page">
                  <Icon size={14} className="breadcrumb-icon" />
                  <span className="breadcrumb-title">{item.title}</span>
                </span>
              ) : (
                <button
                  className="breadcrumb-link"
                  onClick={(e) => handleClick(e, item.path)}
                  title={item.title}
                >
                  <Icon size={14} className="breadcrumb-icon" />
                  <span className="breadcrumb-title">{item.title}</span>
                </button>
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}

export default Breadcrumbs;
