import { Download, ExternalLink, Calendar, HardDrive, Globe } from 'lucide-react';
import type { BuildOutput } from '@/api/types';
import clsx from 'clsx';

// Format icons and colors
const formatStyles: Record<string, { bg: string; text: string }> = {
  pdf: { bg: 'bg-red-500/20', text: 'text-red-500' },
  html: { bg: 'bg-blue-500/20', text: 'text-blue-500' },
  pptx: { bg: 'bg-orange-500/20', text: 'text-orange-500' },
  docx: { bg: 'bg-indigo-500/20', text: 'text-indigo-500' },
  xlsx: { bg: 'bg-green-500/20', text: 'text-green-500' },
  epub: { bg: 'bg-purple-500/20', text: 'text-purple-500' },
  mp4: { bg: 'bg-pink-500/20', text: 'text-pink-500' },
  webm: { bg: 'bg-cyan-500/20', text: 'text-cyan-500' },
};

interface DeliverableCardProps {
  output: BuildOutput;
  onDownload?: (path: string) => void;
  onPreview?: (path: string) => void;
}

export function DeliverableCard({ output, onDownload, onPreview }: DeliverableCardProps) {
  const style = formatStyles[output.format.toLowerCase()] || {
    bg: 'bg-primary/20',
    text: 'text-primary',
  };

  const formattedSize = output.size < 1024 * 1024
    ? `${(output.size / 1024).toFixed(1)} KB`
    : `${(output.size / 1024 / 1024).toFixed(2)} MB`;

  const formattedDate = new Date(output.modified).toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });

  return (
    <div className="card bg-base-200 shadow-sm hover:shadow-md transition-shadow">
      <div className="card-body p-4">
        <div className="flex items-start gap-4">
          {/* Format badge */}
          <div className={clsx('p-3 rounded-lg', style.bg)}>
            <span className={clsx('text-xl font-bold uppercase', style.text)}>
              {output.format}
            </span>
          </div>

          {/* Info */}
          <div className="flex-1 min-w-0">
            <h4 className="font-semibold truncate">{output.name}</h4>
            <div className="flex flex-wrap items-center gap-3 mt-2 text-sm text-base-content/60">
              <span className="flex items-center gap-1">
                <Globe size={12} />
                {output.language.toUpperCase()}
              </span>
              <span className="flex items-center gap-1">
                <HardDrive size={12} />
                {formattedSize}
              </span>
              <span className="flex items-center gap-1">
                <Calendar size={12} />
                {formattedDate}
              </span>
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-2">
            {output.format.toLowerCase() === 'html' && onPreview && (
              <button
                className="btn btn-ghost btn-sm btn-square"
                onClick={() => onPreview(output.path)}
                title="Preview"
              >
                <ExternalLink size={16} />
              </button>
            )}
            {onDownload && (
              <button
                className="btn btn-primary btn-sm btn-square"
                onClick={() => onDownload(output.path)}
                title="Download"
              >
                <Download size={16} />
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
