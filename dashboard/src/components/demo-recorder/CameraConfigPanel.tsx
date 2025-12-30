/**
 * CameraConfigPanel - Right sidebar for camera configuration
 *
 * Features:
 * - Mode toggle (Static/Animated)
 * - Preset picker with descriptions
 * - Capture settings (scale, background)
 * - Focus sequence keyframe editor
 */

import { useState, useEffect } from 'react';
import {
  Settings2,
  Video,
  Camera,
  ChevronDown,
  Plus,
  Trash2,
  GripVertical,
  ZoomIn,
  Clock,
  Pause,
} from 'lucide-react';
import clsx from 'clsx';
import { useCameraPresets, useCameraEasings } from '@/hooks/useVideoApi';
import type { DemoScene, CameraKeyframe, CameraData } from './types';

interface CameraConfigPanelProps {
  scene: DemoScene | null;
  onConfigChange?: (config: Partial<CameraData>) => void;
}

const CAPTURE_SCALES = [
  { value: 1.0, label: '1x', description: 'Standard' },
  { value: 1.5, label: '1.5x', description: 'High Detail' },
  { value: 2.0, label: '2x', description: 'Retina' },
  { value: 3.0, label: '3x', description: 'Ultra HD' },
];

const BACKGROUND_OPTIONS = [
  { value: '#1a1a2e', label: 'Dark Blue', color: '#1a1a2e' },
  { value: '#0f0f0f', label: 'Near Black', color: '#0f0f0f' },
  { value: '#1e1e1e', label: 'Dark Gray', color: '#1e1e1e' },
  { value: '#f5f5f5', label: 'Light Gray', color: '#f5f5f5' },
  { value: 'transparent', label: 'Transparent', color: 'transparent' },
];

export function CameraConfigPanel({ scene, onConfigChange: _onConfigChange }: CameraConfigPanelProps) {
  const { data: presetsData, isLoading: presetsLoading } = useCameraPresets();
  const { data: easingsData } = useCameraEasings();

  // Local state for editing
  const [mode, setMode] = useState<'static' | 'animated'>('animated');
  const [selectedPreset, setSelectedPreset] = useState<string>('guided_tour');
  const [captureScale, setCaptureScale] = useState<number>(2.0);
  const [background, setBackground] = useState<string>('#1a1a2e');
  const [keyframes, setKeyframes] = useState<CameraKeyframe[]>([]);

  // Load from scene cameraData when scene changes
  useEffect(() => {
    if (scene?.cameraData) {
      setMode(scene.cameraData.mode === 'static' ? 'static' : 'animated');
      setCaptureScale(scene.cameraData.capture_scale || 2.0);
      setBackground(scene.cameraData.background || '#1a1a2e');
      setKeyframes(scene.cameraData.keyframes || []);
    } else {
      // Default keyframes for new scenes
      setKeyframes([
        { frame: 0, centerX: 960, centerY: 540, zoom: 1.0, easing: 'easeOutCubic' },
      ]);
    }
  }, [scene]);

  const handlePresetChange = (presetId: string) => {
    setSelectedPreset(presetId);
    const preset = presetsData?.presets.find((p) => p.id === presetId);
    if (preset) {
      // Apply preset defaults to keyframes
      const newKeyframes = keyframes.map((kf, idx) => ({
        ...kf,
        zoom: idx === 0 ? preset.start_zoom : preset.default_zoom,
        easing: preset.default_easing,
        holdFrames: preset.default_hold * 30, // Convert seconds to frames at 30fps
      }));
      setKeyframes(newKeyframes);
    }
  };

  const addKeyframe = () => {
    const lastKf = keyframes[keyframes.length - 1];
    const newFrame = lastKf ? lastKf.frame + 60 : 0; // 2 seconds after last
    setKeyframes([
      ...keyframes,
      {
        frame: newFrame,
        centerX: 960,
        centerY: 540,
        zoom: 1.5,
        easing: easingsData?.recommended || 'easeInOutCubic',
        holdFrames: 30,
      },
    ]);
  };

  const removeKeyframe = (index: number) => {
    if (keyframes.length > 1) {
      setKeyframes(keyframes.filter((_, i) => i !== index));
    }
  };

  const updateKeyframe = (index: number, updates: Partial<CameraKeyframe>) => {
    setKeyframes(keyframes.map((kf, i) => (i === index ? { ...kf, ...updates } : kf)));
  };

  if (!scene) {
    return (
      <div className="h-full flex items-center justify-center text-base-content/50">
        <div className="text-center p-4">
          <Settings2 size={32} className="mx-auto mb-2 opacity-50" />
          <p className="text-sm">Select a scene to configure camera</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-3 border-b border-base-300">
        <h3 className="text-sm font-semibold text-base-content/70 uppercase tracking-wider flex items-center gap-2">
          <Camera size={14} />
          Camera Config
        </h3>
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-4">
        {/* Mode Toggle */}
        <div>
          <label className="text-xs text-base-content/60 mb-2 block">Mode</label>
          <div className="flex gap-1 bg-base-300 rounded-lg p-1">
            <button
              className={clsx('flex-1 py-1.5 px-3 rounded-md text-sm font-medium transition-colors', {
                'bg-primary text-primary-content': mode === 'static',
                'text-base-content/70 hover:text-base-content': mode !== 'static',
              })}
              onClick={() => setMode('static')}
            >
              <Video size={14} className="inline mr-1.5" />
              Static
            </button>
            <button
              className={clsx('flex-1 py-1.5 px-3 rounded-md text-sm font-medium transition-colors', {
                'bg-primary text-primary-content': mode === 'animated',
                'text-base-content/70 hover:text-base-content': mode !== 'animated',
              })}
              onClick={() => setMode('animated')}
            >
              <Camera size={14} className="inline mr-1.5" />
              Animated
            </button>
          </div>
        </div>

        {/* Preset Picker */}
        {mode === 'animated' && (
          <div>
            <label className="text-xs text-base-content/60 mb-2 block">Camera Preset</label>
            <div className="relative">
              <select
                className="select select-sm select-bordered w-full"
                value={selectedPreset}
                onChange={(e) => handlePresetChange(e.target.value)}
                disabled={presetsLoading}
              >
                {presetsData?.presets.map((preset) => (
                  <option key={preset.id} value={preset.id}>
                    {preset.name}
                  </option>
                ))}
              </select>
              <ChevronDown size={14} className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-base-content/50" />
            </div>
            {presetsData?.presets.find((p) => p.id === selectedPreset) && (
              <p className="text-xs text-base-content/50 mt-1">
                {presetsData.presets.find((p) => p.id === selectedPreset)?.description}
              </p>
            )}
          </div>
        )}

        {/* Capture Settings */}
        <div className="space-y-3">
          <h4 className="text-xs text-base-content/60 font-medium">Capture Settings</h4>

          {/* Scale */}
          <div>
            <label className="text-xs text-base-content/50 mb-1.5 block">Scale</label>
            <div className="flex gap-1">
              {CAPTURE_SCALES.map((scale) => (
                <button
                  key={scale.value}
                  className={clsx('flex-1 py-1 px-2 rounded text-xs font-medium transition-colors', {
                    'bg-primary text-primary-content': captureScale === scale.value,
                    'bg-base-300 text-base-content/70 hover:bg-base-200': captureScale !== scale.value,
                  })}
                  onClick={() => setCaptureScale(scale.value)}
                  title={scale.description}
                >
                  {scale.label}
                </button>
              ))}
            </div>
          </div>

          {/* Background */}
          <div>
            <label className="text-xs text-base-content/50 mb-1.5 block">Background</label>
            <div className="flex gap-1.5">
              {BACKGROUND_OPTIONS.map((bg) => (
                <button
                  key={bg.value}
                  className={clsx(
                    'w-7 h-7 rounded border-2 transition-all',
                    bg.value === 'transparent' ? 'bg-checkerboard' : '',
                    {
                      'border-primary ring-2 ring-primary/30': background === bg.value,
                      'border-base-300 hover:border-base-content/30': background !== bg.value,
                    }
                  )}
                  style={{ backgroundColor: bg.value !== 'transparent' ? bg.color : undefined }}
                  onClick={() => setBackground(bg.value)}
                  title={bg.label}
                />
              ))}
            </div>
          </div>
        </div>

        {/* Focus Sequence (Keyframes) */}
        {mode === 'animated' && (
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <h4 className="text-xs text-base-content/60 font-medium">Focus Sequence</h4>
              <button
                className="btn btn-xs btn-ghost gap-1"
                onClick={addKeyframe}
              >
                <Plus size={12} />
                Add
              </button>
            </div>

            <div className="space-y-2">
              {keyframes.map((kf, index) => (
                <div
                  key={index}
                  className="bg-base-300 rounded-lg p-2.5 space-y-2"
                >
                  {/* Keyframe Header */}
                  <div className="flex items-center gap-2">
                    <GripVertical size={12} className="text-base-content/30 cursor-grab" />
                    <span className="text-xs font-medium flex-1">
                      Keyframe {index + 1}
                    </span>
                    {keyframes.length > 1 && (
                      <button
                        className="btn btn-xs btn-ghost btn-square text-error/70 hover:text-error"
                        onClick={() => removeKeyframe(index)}
                      >
                        <Trash2 size={12} />
                      </button>
                    )}
                  </div>

                  {/* Keyframe Controls */}
                  <div className="grid grid-cols-2 gap-2">
                    {/* Zoom */}
                    <div>
                      <label className="text-[10px] text-base-content/50 flex items-center gap-1 mb-0.5">
                        <ZoomIn size={10} />
                        Zoom
                      </label>
                      <input
                        type="number"
                        className="input input-xs input-bordered w-full"
                        value={kf.zoom}
                        onChange={(e) => updateKeyframe(index, { zoom: parseFloat(e.target.value) || 1 })}
                        min={0.5}
                        max={4}
                        step={0.1}
                      />
                    </div>

                    {/* Duration (converted from frames) */}
                    <div>
                      <label className="text-[10px] text-base-content/50 flex items-center gap-1 mb-0.5">
                        <Clock size={10} />
                        Duration
                      </label>
                      <input
                        type="number"
                        className="input input-xs input-bordered w-full"
                        value={(kf.frame / 30).toFixed(1)}
                        onChange={(e) => updateKeyframe(index, { frame: Math.round(parseFloat(e.target.value) * 30) })}
                        min={0}
                        step={0.5}
                        placeholder="sec"
                      />
                    </div>

                    {/* Hold */}
                    <div>
                      <label className="text-[10px] text-base-content/50 flex items-center gap-1 mb-0.5">
                        <Pause size={10} />
                        Hold
                      </label>
                      <input
                        type="number"
                        className="input input-xs input-bordered w-full"
                        value={((kf.holdFrames || 0) / 30).toFixed(1)}
                        onChange={(e) => updateKeyframe(index, { holdFrames: Math.round(parseFloat(e.target.value) * 30) })}
                        min={0}
                        step={0.5}
                        placeholder="sec"
                      />
                    </div>

                    {/* Easing */}
                    <div>
                      <label className="text-[10px] text-base-content/50 mb-0.5 block">Easing</label>
                      <select
                        className="select select-xs select-bordered w-full"
                        value={kf.easing || 'easeInOutCubic'}
                        onChange={(e) => updateKeyframe(index, { easing: e.target.value })}
                      >
                        {easingsData?.easings.map((easing) => (
                          <option key={easing.name} value={easing.name}>
                            {easing.name.replace('ease', '')}
                            {easing.recommended ? ' *' : ''}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>

                  {/* Position (read-only for now) */}
                  <div className="text-[10px] text-base-content/40 pt-1 border-t border-base-200">
                    Position: {Math.round(kf.centerX)}, {Math.round(kf.centerY)}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
