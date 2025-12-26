import { BookOpen, Presentation, Table, FileSpreadsheet, CheckCircle } from 'lucide-react';
import type { PublicationBuildInfo } from '@/api/types';

const typeIcons = {
  book: BookOpen,
  deck: Presentation,
  spreadsheet: Table,
  report: FileSpreadsheet,
};

const formatLabels: Record<string, string> = {
  html: 'HTML',
  pptx: 'PPTX',
  xlsx: 'XLSX',
  pdf: 'PDF',
};

const formatColors: Record<string, { active: string; inactive: string }> = {
  html: { active: 'badge-info', inactive: 'badge-outline opacity-50' },
  pptx: { active: 'badge-warning', inactive: 'badge-outline opacity-50' },
  xlsx: { active: 'badge-success', inactive: 'badge-outline opacity-50' },
  pdf: { active: 'badge-error', inactive: 'badge-outline opacity-50' },
};

interface PublicationCardProps {
  publication: PublicationBuildInfo;
  selected: boolean;
  selectedFormats: string[];
  selectedLanguages: string[];
  onToggleSelect: () => void;
  onToggleFormat: (format: string) => void;
  onToggleLanguage: (language: string) => void;
  disabled?: boolean;
}

export function PublicationCard({
  publication,
  selected,
  selectedFormats,
  selectedLanguages,
  onToggleSelect,
  onToggleFormat,
  onToggleLanguage,
  disabled = false,
}: PublicationCardProps) {
  const Icon = typeIcons[publication.pub_type] || BookOpen;

  return (
    <div
      className={`rounded-lg border-2 p-4 transition-all ${
        selected
          ? 'bg-primary/10 border-primary'
          : 'bg-base-200 border-transparent hover:bg-base-300'
      } ${disabled ? 'opacity-50' : ''}`}
    >
      {/* Header row with checkbox and title */}
      <div className="flex items-start gap-3">
        <label className="cursor-pointer flex items-center">
          <input
            type="checkbox"
            className="checkbox checkbox-primary"
            checked={selected}
            onChange={onToggleSelect}
            disabled={disabled}
          />
        </label>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <Icon size={18} className="text-base-content/60 shrink-0" />
            <h4 className="font-medium truncate">{publication.title}</h4>
          </div>
          <div className="text-xs text-base-content/50 capitalize mt-0.5">
            {publication.pub_type}
          </div>
        </div>
        {selected && <CheckCircle size={18} className="text-primary shrink-0" />}
      </div>

      {/* Languages */}
      <div className="flex flex-wrap gap-1 mt-3">
        {publication.languages.map((lang) => {
          const isActive = selectedLanguages.includes(lang);
          return (
            <button
              key={lang}
              className={`badge badge-sm transition-all ${
                isActive && selected
                  ? 'badge-success'
                  : selected
                  ? 'badge-outline hover:badge-success'
                  : 'badge-ghost'
              }`}
              onClick={(e) => {
                e.stopPropagation();
                if (selected) onToggleLanguage(lang);
              }}
              disabled={disabled || !selected}
            >
              {lang.toUpperCase()}
            </button>
          );
        })}
      </div>

      {/* Formats */}
      <div className="flex flex-wrap gap-1 mt-2">
        {publication.formats.map((format) => {
          const isActive = selectedFormats.includes(format);
          const colors = formatColors[format.toLowerCase()] || formatColors.html;
          return (
            <button
              key={format}
              className={`badge badge-sm transition-all ${
                isActive && selected ? colors.active : colors.inactive
              }`}
              onClick={(e) => {
                e.stopPropagation();
                if (selected) onToggleFormat(format);
              }}
              disabled={disabled || !selected}
            >
              {formatLabels[format.toLowerCase()] || format.toUpperCase()}
            </button>
          );
        })}
      </div>

      {/* Stale indicator */}
      {publication.isStale && (
        <div className="mt-2 text-xs text-warning flex items-center gap-1">
          Needs rebuild
        </div>
      )}
    </div>
  );
}
