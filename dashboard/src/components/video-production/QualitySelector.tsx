/**
 * QualitySelector - Toggle between PREVIEW and PRODUCTION quality
 *
 * Features:
 * - Visual comparison of settings
 * - Estimated render time
 * - Clear quality difference indication
 */

import { Monitor, Zap, CheckCircle, Clock, Film } from 'lucide-react';
import { cn } from '@/utils/cn';
import { QUALITY_PRESETS, type VideoQuality } from '@/api/types/video';
import { getVideoQualityBadge } from '@/utils/statusMappings';

// ============================================================================
// Types
// ============================================================================

interface QualitySelectorProps {
  /** Currently selected quality */
  value: VideoQuality;
  /** Change handler */
  onChange: (quality: VideoQuality) => void;
  /** Disabled state */
  disabled?: boolean;
  /** Show detailed comparison */
  showDetails?: boolean;
  /** Compact mode (dropdown instead of cards) */
  compact?: boolean;
  /** Additional className */
  className?: string;
}

// ============================================================================
// Compact Selector (Dropdown)
// ============================================================================

function CompactQualitySelector({
  value,
  onChange,
  disabled,
  className,
}: Omit<QualitySelectorProps, 'showDetails' | 'compact'>) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value as VideoQuality)}
      disabled={disabled}
      className={cn('select select-bordered select-sm', className)}
    >
      {Object.entries(QUALITY_PRESETS).map(([key, preset]) => (
        <option key={key} value={key}>
          {preset.name} ({preset.width}x{preset.height}, {preset.fps}fps)
        </option>
      ))}
    </select>
  );
}

// ============================================================================
// Quality Card
// ============================================================================

interface QualityCardProps {
  preset: typeof QUALITY_PRESETS.preview;
  isSelected: boolean;
  onClick: () => void;
  disabled?: boolean;
}

function QualityCard({ preset, isSelected, onClick, disabled }: QualityCardProps) {
  const Icon = preset.id === 'preview' ? Zap : Film;

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={cn(
        'flex-1 p-4 rounded-lg border-2 transition-all text-left',
        isSelected
          ? 'border-primary bg-primary/10 ring-2 ring-primary ring-offset-2 ring-offset-base-100'
          : 'border-base-300 bg-base-200 hover:border-base-content/30',
        disabled && 'opacity-50 cursor-not-allowed'
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Icon
            size={20}
            className={cn(
              preset.id === 'preview' ? 'text-warning' : 'text-success'
            )}
          />
          <span className="font-semibold">{preset.name}</span>
        </div>
        {isSelected && <CheckCircle size={18} className="text-primary" />}
      </div>

      {/* Description */}
      <p className="text-sm text-base-content/60 mb-3">
        {preset.description}
      </p>

      {/* Specs */}
      <div className="grid grid-cols-2 gap-2 text-xs">
        <div className="flex items-center gap-1.5">
          <Monitor size={12} className="text-base-content/40" />
          <span className="font-mono">
            {preset.width}x{preset.height}
          </span>
        </div>
        <div className="flex items-center gap-1.5">
          <Film size={12} className="text-base-content/40" />
          <span className="font-mono">{preset.fps} fps</span>
        </div>
        <div className="flex items-center gap-1.5">
          <Clock size={12} className="text-base-content/40" />
          <span>{preset.estimatedTime}</span>
        </div>
        <div>
          <span
            className={cn(
              'badge badge-xs',
              getVideoQualityBadge(preset.id)
            )}
          >
            CRF {preset.crf}
          </span>
        </div>
      </div>
    </button>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export function QualitySelector({
  value,
  onChange,
  disabled = false,
  showDetails = true,
  compact = false,
  className,
}: QualitySelectorProps) {
  if (compact) {
    return (
      <CompactQualitySelector
        value={value}
        onChange={onChange}
        disabled={disabled}
        className={className}
      />
    );
  }

  return (
    <div className={cn('space-y-3', className)}>
      {/* Card selector */}
      <div className="flex gap-4">
        <QualityCard
          preset={QUALITY_PRESETS.preview}
          isSelected={value === 'preview'}
          onClick={() => onChange('preview')}
          disabled={disabled}
        />
        <QualityCard
          preset={QUALITY_PRESETS.production}
          isSelected={value === 'production'}
          onClick={() => onChange('production')}
          disabled={disabled}
        />
      </div>

      {/* Details comparison */}
      {showDetails && (
        <div className="bg-base-200 rounded-lg p-3">
          <div className="text-xs text-base-content/60 mb-2">
            Selected: <strong>{QUALITY_PRESETS[value].name}</strong>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span>
              {QUALITY_PRESETS[value].width} x {QUALITY_PRESETS[value].height} @{' '}
              {QUALITY_PRESETS[value].fps}fps
            </span>
            <span className="flex items-center gap-1">
              <Clock size={14} />
              {QUALITY_PRESETS[value].estimatedTime}
            </span>
          </div>
          {value === 'preview' && (
            <p className="text-xs text-warning mt-2">
              Preview quality is not suitable for release. Use Production for final output.
            </p>
          )}
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Simple Toggle (for inline use)
// ============================================================================

interface QualityToggleProps {
  value: VideoQuality;
  onChange: (quality: VideoQuality) => void;
  disabled?: boolean;
  className?: string;
}

export function QualityToggle({
  value,
  onChange,
  disabled,
  className,
}: QualityToggleProps) {
  return (
    <div className={cn('join', className)}>
      <button
        onClick={() => onChange('preview')}
        disabled={disabled}
        className={cn(
          'join-item btn btn-sm',
          value === 'preview' ? 'btn-warning' : 'btn-ghost'
        )}
      >
        <Zap size={14} />
        Preview
      </button>
      <button
        onClick={() => onChange('production')}
        disabled={disabled}
        className={cn(
          'join-item btn btn-sm',
          value === 'production' ? 'btn-success' : 'btn-ghost'
        )}
      >
        <Film size={14} />
        Production
      </button>
    </div>
  );
}

export default QualitySelector;
