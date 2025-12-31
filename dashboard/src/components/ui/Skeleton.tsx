import type { HTMLAttributes } from 'react';
import clsx from 'clsx';

interface SkeletonProps extends HTMLAttributes<HTMLDivElement> {
  width?: string | number;
  height?: string | number;
  variant?: 'text' | 'circular' | 'rectangular' | 'rounded';
}

const variantStyles = {
  text: 'rounded',
  circular: 'rounded-full',
  rectangular: '',
  rounded: 'rounded-lg',
};

export function Skeleton({
  width,
  height,
  variant = 'text',
  className,
  style: styleProp,
  ...props
}: SkeletonProps) {
  const style: React.CSSProperties = { ...styleProp };
  if (width) style.width = typeof width === 'number' ? `${width}px` : width;
  if (height) style.height = typeof height === 'number' ? `${height}px` : height;

  return (
    <div
      className={clsx('skeleton bg-base-300', variantStyles[variant], className)}
      style={style}
      {...props}
    />
  );
}

// SkeletonText - Multiple lines of text with shimmer animation
interface SkeletonTextProps extends HTMLAttributes<HTMLDivElement> {
  lines?: number;
  lineHeight?: number;
  spacing?: number;
  lastLineWidth?: string;
}

export function SkeletonText({
  lines = 3,
  lineHeight = 14,
  spacing = 8,
  lastLineWidth = '75%',
  className,
  ...props
}: SkeletonTextProps) {
  return (
    <div className={clsx('space-y-2', className)} style={{ gap: spacing }} {...props}>
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton
          key={i}
          width={i === lines - 1 ? lastLineWidth : '100%'}
          height={lineHeight}
        />
      ))}
    </div>
  );
}

// SkeletonAvatar - Circular placeholder for avatars/profile images
interface SkeletonAvatarProps extends Omit<HTMLAttributes<HTMLDivElement>, 'children'> {
  size?: 'sm' | 'md' | 'lg' | 'xl';
}

const avatarSizes = {
  sm: 24,
  md: 40,
  lg: 56,
  xl: 80,
};

export function SkeletonAvatar({ size = 'md', className, ...props }: SkeletonAvatarProps) {
  const pixelSize = avatarSizes[size];
  return (
    <Skeleton
      variant="circular"
      width={pixelSize}
      height={pixelSize}
      className={className}
      {...props}
    />
  );
}

// SkeletonTable - Table rows placeholder
interface SkeletonTableProps extends HTMLAttributes<HTMLDivElement> {
  rows?: number;
  columns?: number;
  showHeader?: boolean;
}

export function SkeletonTable({
  rows = 5,
  columns = 4,
  showHeader = true,
  className,
  ...props
}: SkeletonTableProps) {
  return (
    <div className={clsx('w-full', className)} {...props}>
      {/* Table header */}
      {showHeader && (
        <div className="flex gap-4 py-3 border-b border-base-300">
          {Array.from({ length: columns }).map((_, i) => (
            <div key={`header-${i}`} className="flex-1">
              <Skeleton width="60%" height={12} />
            </div>
          ))}
        </div>
      )}
      {/* Table rows */}
      {Array.from({ length: rows }).map((_, rowIndex) => (
        <div
          key={`row-${rowIndex}`}
          className="flex gap-4 py-3 border-b border-base-300/50"
        >
          {Array.from({ length: columns }).map((_, colIndex) => (
            <div key={`cell-${rowIndex}-${colIndex}`} className="flex-1">
              <Skeleton
                width={colIndex === 0 ? '80%' : '60%'}
                height={14}
              />
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}

// Pre-built skeleton patterns
export function SkeletonCard() {
  return (
    <div className="card bg-base-200 p-4 space-y-3">
      <div className="flex items-center gap-3">
        <Skeleton variant="circular" width={40} height={40} />
        <div className="space-y-2">
          <Skeleton width={120} height={14} />
          <Skeleton width={80} height={12} />
        </div>
      </div>
      <Skeleton width="100%" height={12} />
      <Skeleton width="90%" height={12} />
      <Skeleton width="75%" height={12} />
    </div>
  );
}

export function SkeletonList({ count = 5 }: { count?: number }) {
  return (
    <div className="space-y-2">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="flex items-center gap-3 p-2">
          <Skeleton variant="rounded" width={32} height={32} />
          <div className="flex-1 space-y-2">
            <Skeleton width="60%" height={14} />
            <Skeleton width="40%" height={12} />
          </div>
        </div>
      ))}
    </div>
  );
}

export function SkeletonStats() {
  return (
    <div className="grid grid-cols-4 gap-4">
      {Array.from({ length: 4 }).map((_, i) => (
        <div key={i} className="card bg-base-200 p-4 space-y-2">
          <Skeleton width={80} height={12} />
          <Skeleton width={60} height={32} />
        </div>
      ))}
    </div>
  );
}
