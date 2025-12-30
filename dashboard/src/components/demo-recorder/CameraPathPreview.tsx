/**
 * CameraPathPreview - Canvas-based camera path visualization
 *
 * Displays:
 * - Demo screenshot as background
 * - Keyframe markers (numbered circles)
 * - Spline path between keyframes
 * - Viewport rectangle showing camera view
 * - Current position indicator during playback
 */

import { useRef, useEffect, useState, useMemo } from 'react';
import { ZoomIn, Move, Eye } from 'lucide-react';
import type { DemoScene, CameraKeyframe } from './types';

interface CameraPathPreviewProps {
  scene: DemoScene;
  propsData: any;
  currentFrame: number;
  isPlaying: boolean;
}

// Catmull-Rom spline interpolation (matches Remotion)
function catmullRomPoint(
  p0: { x: number; y: number },
  p1: { x: number; y: number },
  p2: { x: number; y: number },
  p3: { x: number; y: number },
  t: number
): { x: number; y: number } {
  const t2 = t * t;
  const t3 = t2 * t;

  const x =
    0.5 *
    (2 * p1.x +
      (-p0.x + p2.x) * t +
      (2 * p0.x - 5 * p1.x + 4 * p2.x - p3.x) * t2 +
      (-p0.x + 3 * p1.x - 3 * p2.x + p3.x) * t3);

  const y =
    0.5 *
    (2 * p1.y +
      (-p0.y + p2.y) * t +
      (2 * p0.y - 5 * p1.y + 4 * p2.y - p3.y) * t2 +
      (-p0.y + 3 * p1.y - 3 * p2.y + p3.y) * t3);

  return { x, y };
}

// Generate spline path points
function generateSplinePath(keyframes: CameraKeyframe[], steps: number = 50): { x: number; y: number }[] {
  if (keyframes.length < 2) {
    return keyframes.map((kf) => ({ x: kf.centerX, y: kf.centerY }));
  }

  const points: { x: number; y: number }[] = [];
  const kfPoints = keyframes.map((kf) => ({ x: kf.centerX, y: kf.centerY }));

  for (let i = 0; i < kfPoints.length - 1; i++) {
    const p0 = kfPoints[Math.max(0, i - 1)];
    const p1 = kfPoints[i];
    const p2 = kfPoints[i + 1];
    const p3 = kfPoints[Math.min(kfPoints.length - 1, i + 2)];

    for (let j = 0; j < steps; j++) {
      const t = j / steps;
      points.push(catmullRomPoint(p0, p1, p2, p3, t));
    }
  }

  // Add final point
  points.push(kfPoints[kfPoints.length - 1]);
  return points;
}

export function CameraPathPreview({
  scene,
  propsData: _propsData,
  currentFrame,
  isPlaying,
}: CameraPathPreviewProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [canvasSize, setCanvasSize] = useState({ width: 800, height: 450 });
  // Reserved for future screenshot loading
  // const [_imageLoaded, _setImageLoaded] = useState(false);
  // const _imageRef = useRef<HTMLImageElement | null>(null);

  // Mock keyframes for demo (will come from cameraData in real implementation)
  const mockKeyframes: CameraKeyframe[] = useMemo(() => {
    // Generate some example keyframes based on scene
    const baseWidth = 1920;
    const baseHeight = 1080;

    return [
      { frame: 0, centerX: baseWidth / 2, centerY: baseHeight / 2, zoom: 1.0, easing: 'easeOutExpo' },
      { frame: 30, centerX: 400, centerY: 300, zoom: 2.0, easing: 'easeInOutCubic', holdFrames: 30 },
      { frame: 90, centerX: 1200, centerY: 600, zoom: 1.8, easing: 'easeInOutCubic', holdFrames: 45 },
      { frame: 180, centerX: baseWidth / 2, centerY: baseHeight / 2, zoom: 1.0, easing: 'easeOutQuart' },
    ];
  }, [scene]);

  // Use actual keyframes from cameraData if available
  const keyframes = (scene as any).cameraData?.keyframes || mockKeyframes;
  const viewportWidth = (scene as any).cameraData?.viewport_width || 1920;
  const viewportHeight = (scene as any).cameraData?.viewport_height || 1080;

  // Resize canvas to fit container
  useEffect(() => {
    const updateSize = () => {
      if (containerRef.current) {
        const rect = containerRef.current.getBoundingClientRect();
        // Maintain 16:9 aspect ratio
        const aspectRatio = 16 / 9;
        let width = rect.width - 32;
        let height = width / aspectRatio;

        if (height > rect.height - 32) {
          height = rect.height - 32;
          width = height * aspectRatio;
        }

        setCanvasSize({ width, height });
      }
    };

    updateSize();
    window.addEventListener('resize', updateSize);
    return () => window.removeEventListener('resize', updateSize);
  }, []);

  // Draw camera path visualization
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const { width, height } = canvasSize;
    const scaleX = width / viewportWidth;
    const scaleY = height / viewportHeight;

    // Clear canvas
    ctx.fillStyle = '#1a1a2e';
    ctx.fillRect(0, 0, width, height);

    // Draw grid
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.05)';
    ctx.lineWidth = 1;
    const gridSize = 50;
    for (let x = 0; x < width; x += gridSize * scaleX) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, height);
      ctx.stroke();
    }
    for (let y = 0; y < height; y += gridSize * scaleY) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(width, y);
      ctx.stroke();
    }

    // Draw spline path
    const pathPoints = generateSplinePath(keyframes);
    if (pathPoints.length > 1) {
      ctx.beginPath();
      ctx.strokeStyle = 'rgba(99, 102, 241, 0.6)';
      ctx.lineWidth = 2;
      ctx.setLineDash([8, 4]);

      ctx.moveTo(pathPoints[0].x * scaleX, pathPoints[0].y * scaleY);
      for (let i = 1; i < pathPoints.length; i++) {
        ctx.lineTo(pathPoints[i].x * scaleX, pathPoints[i].y * scaleY);
      }
      ctx.stroke();
      ctx.setLineDash([]);
    }

    // Draw keyframe markers
    keyframes.forEach((kf: CameraKeyframe, index: number) => {
      const x = kf.centerX * scaleX;
      const y = kf.centerY * scaleY;
      const radius = 20;

      // Draw viewport rectangle at this keyframe
      const viewW = (viewportWidth / kf.zoom) * scaleX;
      const viewH = (viewportHeight / kf.zoom) * scaleY;
      ctx.strokeStyle = index === 0 ? 'rgba(34, 197, 94, 0.4)' : 'rgba(99, 102, 241, 0.3)';
      ctx.lineWidth = 1;
      ctx.strokeRect(x - viewW / 2, y - viewH / 2, viewW, viewH);

      // Draw keyframe circle
      ctx.beginPath();
      ctx.arc(x, y, radius, 0, Math.PI * 2);
      ctx.fillStyle = index === 0 ? '#22c55e' : '#6366f1';
      ctx.fill();
      ctx.strokeStyle = '#fff';
      ctx.lineWidth = 2;
      ctx.stroke();

      // Draw keyframe number
      ctx.fillStyle = '#fff';
      ctx.font = 'bold 12px system-ui';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(String(index + 1), x, y);

      // Draw zoom label
      ctx.font = '10px system-ui';
      ctx.fillStyle = 'rgba(255, 255, 255, 0.7)';
      ctx.fillText(`${kf.zoom.toFixed(1)}x`, x, y + radius + 12);

      // Draw easing label
      if (kf.easing) {
        ctx.font = '9px system-ui';
        ctx.fillStyle = 'rgba(255, 255, 255, 0.5)';
        ctx.fillText(kf.easing.replace('ease', ''), x, y + radius + 24);
      }
    });

    // Draw current position indicator
    if (keyframes.length >= 2) {
      // Find current position on path based on frame
      const totalFrames = keyframes[keyframes.length - 1].frame;
      const progress = Math.min(currentFrame / totalFrames, 1);
      const pathIndex = Math.floor(progress * (pathPoints.length - 1));
      const currentPoint = pathPoints[Math.min(pathIndex, pathPoints.length - 1)];

      if (currentPoint) {
        const x = currentPoint.x * scaleX;
        const y = currentPoint.y * scaleY;

        // Draw current position
        ctx.beginPath();
        ctx.arc(x, y, 8, 0, Math.PI * 2);
        ctx.fillStyle = '#f43f5e';
        ctx.fill();
        ctx.strokeStyle = '#fff';
        ctx.lineWidth = 2;
        ctx.stroke();

        // Draw pulse effect when playing
        if (isPlaying) {
          ctx.beginPath();
          ctx.arc(x, y, 16, 0, Math.PI * 2);
          ctx.strokeStyle = 'rgba(244, 63, 94, 0.5)';
          ctx.lineWidth = 2;
          ctx.stroke();
        }
      }
    }
  }, [canvasSize, keyframes, currentFrame, isPlaying, viewportWidth, viewportHeight]);

  return (
    <div ref={containerRef} className="h-full flex flex-col">
      {/* Canvas Info Bar */}
      <div className="flex items-center justify-between mb-3 text-sm">
        <div className="flex items-center gap-4 text-base-content/60">
          <span className="flex items-center gap-1">
            <Move size={14} />
            {keyframes.length} keyframes
          </span>
          <span className="flex items-center gap-1">
            <ZoomIn size={14} />
            {keyframes.length > 0 && `${keyframes[0].zoom.toFixed(1)}x - ${Math.max(...keyframes.map((k: CameraKeyframe) => k.zoom)).toFixed(1)}x`}
          </span>
          <span className="flex items-center gap-1">
            <Eye size={14} />
            {viewportWidth}x{viewportHeight}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className="badge badge-sm badge-primary">Scene: {scene.id}</span>
        </div>
      </div>

      {/* Canvas */}
      <div className="flex-1 flex items-center justify-center bg-base-300 rounded-lg overflow-hidden">
        <canvas
          ref={canvasRef}
          width={canvasSize.width}
          height={canvasSize.height}
          className="rounded shadow-lg"
        />
      </div>

      {/* Legend */}
      <div className="flex items-center justify-center gap-6 mt-3 text-xs text-base-content/60">
        <span className="flex items-center gap-2">
          <span className="w-3 h-3 rounded-full bg-green-500" />
          Start
        </span>
        <span className="flex items-center gap-2">
          <span className="w-3 h-3 rounded-full bg-indigo-500" />
          Keyframe
        </span>
        <span className="flex items-center gap-2">
          <span className="w-3 h-3 rounded-full bg-rose-500" />
          Current
        </span>
        <span className="flex items-center gap-2">
          <span className="w-6 h-0.5 bg-indigo-500/60" style={{ borderStyle: 'dashed' }} />
          Path
        </span>
      </div>
    </div>
  );
}
