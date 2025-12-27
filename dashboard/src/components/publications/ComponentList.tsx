import { FileText, Image, Film, PieChart, Database, FileCode, Layout } from 'lucide-react';
import type { PublicationChapter } from '@/api/types';

// Component type icons
const componentIcons: Record<string, React.ComponentType<{ size?: number; className?: string }>> = {
  chapter: FileText,
  section: FileText,
  slide: Layout,
  diagram: PieChart,
  asset: Image,
  script: FileCode,
  scene: Film,
  data: Database,
  template: FileCode,
};

interface ComponentListProps {
  components: PublicationChapter[];
  showStatus?: boolean;
  compact?: boolean;
}

export function ComponentList({
  components,
  showStatus = true,
  compact = false,
}: ComponentListProps) {
  if (!components || components.length === 0) {
    return (
      <div className="text-center py-6 text-base-content/60 text-sm">
        No components defined
      </div>
    );
  }

  if (compact) {
    return (
      <ul className="space-y-1">
        {components.map((comp, idx) => {
          const Icon = componentIcons.chapter;
          const filename = comp.path.split('/').pop() || comp.path;
          return (
            <li key={idx} className="flex items-center gap-2 text-sm py-1">
              <Icon size={14} className="text-base-content/50 flex-shrink-0" />
              <span className="truncate flex-1">{filename}</span>
              {!comp.required && (
                <span className="badge badge-xs badge-ghost">optional</span>
              )}
            </li>
          );
        })}
      </ul>
    );
  }

  return (
    <div className="divide-y divide-base-300">
      {components.map((comp, idx) => {
        const Icon = componentIcons.chapter;
        const filename = comp.path.split('/').pop() || comp.path;

        return (
          <div key={idx} className="py-3 flex items-start gap-3">
            <div className="p-2 rounded bg-base-300">
              <Icon size={16} className="text-primary" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="font-medium text-sm truncate">{filename}</p>
              <p className="text-xs text-base-content/60 truncate">{comp.path}</p>
              {comp.sections && comp.sections.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1">
                  {comp.sections.map((section, sIdx) => (
                    <span key={sIdx} className="badge badge-xs badge-ghost">
                      {section}
                    </span>
                  ))}
                </div>
              )}
            </div>
            <div className="flex items-center gap-2">
              {!comp.required && (
                <span className="badge badge-sm badge-warning">Optional</span>
              )}
              {showStatus && (
                <span className="badge badge-sm badge-success">Ready</span>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
