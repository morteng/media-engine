/**
 * SceneCard - Consistent card for scene display
 *
 * Features:
 * - Type-colored badge and border
 * - Duration and frame range display
 * - Voiceover preview (truncated)
 * - Click to select, visual indicator for current
 * - Compact and expanded modes
 */

import { Clock, MessageSquare } from 'lucide-react';
import { cn } from '@/utils/cn';
import { getSceneTypeColors, getSceneTypeBadge } from '@/utils/statusMappings';
import type { UnifiedScene } from '@/api/types/video';

// ============================================================================
// Types
// ============================================================================

interface SceneCardProps {
  scene: UnifiedScene;
  /** Whether this scene is selected */
  isSelected?: boolean;
  /** Whether this scene is currently playing */
  isCurrent?: boolean;
  /** FPS for time calculations */
  fps?: number;
  /** Click handler */
  onClick?: () => void;
  /** Compact mode (less detail) */
  compact?: boolean;
  /** Show frame numbers instead of time */
  showFrames?: boolean;
  /** Additional className */
  className?: string;
}

// ============================================================================
// Helpers
// ============================================================================

function formatDuration(seconds: number): string {
  if (seconds < 60) {
    return `${seconds.toFixed(1)}s`;
  }
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}:${secs.toFixed(0).padStart(2, '0')}`;
}

function formatFrameRange(start: number, end: number): string {
  return `${start} - ${end}`;
}

function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength - 3) + '...';
}

// ============================================================================
// Component
// ============================================================================

export function SceneCard({
  scene,
  isSelected = false,
  isCurrent = false,
  fps = 30,
  onClick,
  compact = false,
  showFrames = false,
  className,
}: SceneCardProps) {
  const colors = getSceneTypeColors(scene.type);
  const badgeClass = getSceneTypeBadge(scene.type);

  // Calculate duration
  const durationSeconds = scene.durationFrames
    ? scene.durationFrames / fps
    : scene.duration || 0;

  // Voiceover text (use text or voiceover field)
  const voiceoverText = scene.text || scene.voiceover;

  return (
    <div
      onClick={onClick}
      className={cn(
        'rounded-lg border-2 transition-all duration-200',
        colors.bg,
        colors.border,
        onClick && 'cursor-pointer hover:scale-[1.02]',
        isSelected && 'ring-2 ring-primary ring-offset-2 ring-offset-base-100',
        isCurrent && 'animate-pulse',
        className
      )}
    >
      <div className={cn('p-3', compact && 'p-2')}>
        {/* Header: Type badge + Duration */}
        <div className="flex items-center justify-between gap-2 mb-2">
          <span className={cn('badge badge-sm', badgeClass)}>
            {scene.type}
          </span>
          <div className="flex items-center gap-1 text-xs text-base-content/60">
            <Clock size={12} />
            {showFrames && scene.startFrame !== undefined && scene.endFrame !== undefined ? (
              <span className="font-mono">
                {formatFrameRange(scene.startFrame, scene.endFrame)}
              </span>
            ) : (
              <span>{formatDuration(durationSeconds)}</span>
            )}
          </div>
        </div>

        {/* Title */}
        {(scene.title || scene.name) && (
          <h4 className={cn(
            'font-medium',
            colors.text,
            compact ? 'text-sm' : 'text-base'
          )}>
            {scene.title || scene.name}
          </h4>
        )}

        {/* Voiceover preview (not in compact mode) */}
        {!compact && voiceoverText && (
          <div className="mt-2 flex items-start gap-2">
            <MessageSquare size={14} className="text-base-content/40 mt-0.5 shrink-0" />
            <p className="text-sm text-base-content/60 line-clamp-2">
              {truncateText(voiceoverText, 100)}
            </p>
          </div>
        )}

        {/* Visual info (not in compact mode) */}
        {!compact && scene.visual && (
          <div className="mt-2 flex flex-wrap gap-1">
            {scene.visual.background && (
              <span className="badge badge-xs badge-ghost">
                {scene.visual.background}
              </span>
            )}
            {scene.visual.transition_in && (
              <span className="badge badge-xs badge-ghost">
                {scene.visual.transition_in}
              </span>
            )}
            {scene.visual.text_effect && (
              <span className="badge badge-xs badge-ghost">
                {scene.visual.text_effect}
              </span>
            )}
          </div>
        )}

        {/* Frame info (compact mode shows inline) */}
        {compact && scene.durationFrames && (
          <div className="mt-1 text-xs text-base-content/40 font-mono">
            {scene.durationFrames} frames
          </div>
        )}
      </div>

      {/* Current indicator bar */}
      {isCurrent && (
        <div className={cn('h-1 rounded-b-lg', colors.border.replace('border-', 'bg-'))} />
      )}
    </div>
  );
}

// ============================================================================
// Scene List Component
// ============================================================================

interface SceneListProps {
  scenes: UnifiedScene[];
  selectedSceneId?: string | null;
  currentSceneId?: string | null;
  fps?: number;
  onSelectScene?: (sceneId: string) => void;
  compact?: boolean;
  showFrames?: boolean;
  className?: string;
}

export function SceneList({
  scenes,
  selectedSceneId,
  currentSceneId,
  fps = 30,
  onSelectScene,
  compact = false,
  showFrames = false,
  className,
}: SceneListProps) {
  return (
    <div className={cn('space-y-2', className)}>
      {scenes.map((scene) => (
        <SceneCard
          key={scene.id}
          scene={scene}
          isSelected={selectedSceneId === scene.id}
          isCurrent={currentSceneId === scene.id}
          fps={fps}
          onClick={() => onSelectScene?.(scene.id)}
          compact={compact}
          showFrames={showFrames}
        />
      ))}
    </div>
  );
}

// ============================================================================
// Scene Grid Component
// ============================================================================

interface SceneGridProps extends SceneListProps {
  columns?: 2 | 3 | 4;
}

export function SceneGrid({
  scenes,
  selectedSceneId,
  currentSceneId,
  fps = 30,
  onSelectScene,
  compact = false,
  showFrames = false,
  columns = 3,
  className,
}: SceneGridProps) {
  const gridCols = {
    2: 'grid-cols-1 md:grid-cols-2',
    3: 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3',
    4: 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4',
  };

  return (
    <div className={cn('grid gap-3', gridCols[columns], className)}>
      {scenes.map((scene) => (
        <SceneCard
          key={scene.id}
          scene={scene}
          isSelected={selectedSceneId === scene.id}
          isCurrent={currentSceneId === scene.id}
          fps={fps}
          onClick={() => onSelectScene?.(scene.id)}
          compact={compact}
          showFrames={showFrames}
        />
      ))}
    </div>
  );
}

export default SceneCard;
