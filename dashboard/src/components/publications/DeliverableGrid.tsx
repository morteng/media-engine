import { DeliverableCard } from './DeliverableCard';
import { FileOutput, Package } from 'lucide-react';
import type { BuildOutput } from '@/api/types';

interface DeliverableGridProps {
  outputs: BuildOutput[];
  onDownload?: (path: string) => void;
  onPreview?: (path: string) => void;
  groupByFormat?: boolean;
  emptyMessage?: string;
}

export function DeliverableGrid({
  outputs,
  onDownload,
  onPreview,
  groupByFormat = false,
  emptyMessage = 'No deliverables available. Build a publication to generate outputs.',
}: DeliverableGridProps) {
  if (!outputs || outputs.length === 0) {
    return (
      <div className="text-center py-12">
        <Package size={48} className="mx-auto text-base-content/30 mb-4" />
        <p className="text-base-content/60">{emptyMessage}</p>
      </div>
    );
  }

  if (groupByFormat) {
    // Group by format
    const byFormat = outputs.reduce((acc, output) => {
      const format = output.format.toLowerCase();
      if (!acc[format]) acc[format] = [];
      acc[format].push(output);
      return acc;
    }, {} as Record<string, BuildOutput[]>);

    return (
      <div className="space-y-6">
        {Object.entries(byFormat).map(([format, items]) => (
          <div key={format}>
            <h3 className="text-sm font-semibold text-base-content/70 mb-3 uppercase tracking-wide flex items-center gap-2">
              <FileOutput size={14} />
              {format}
              <span className="badge badge-xs">{items.length}</span>
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {items.map((output, idx) => (
                <DeliverableCard
                  key={`${output.path}-${idx}`}
                  output={output}
                  onDownload={onDownload}
                  onPreview={onPreview}
                />
              ))}
            </div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {outputs.map((output, idx) => (
        <DeliverableCard
          key={`${output.path}-${idx}`}
          output={output}
          onDownload={onDownload}
          onPreview={onPreview}
        />
      ))}
    </div>
  );
}
