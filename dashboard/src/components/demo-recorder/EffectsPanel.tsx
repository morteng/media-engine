/**
 * EffectsPanel - Visual effects configuration
 *
 * Features:
 * - Effects preset dropdown
 * - Toggle + intensity slider for each effect
 * - Live preview updates (via callback)
 */

import { useState, useEffect } from 'react';
import { Sparkles, ChevronDown, Eye, EyeOff } from 'lucide-react';
import clsx from 'clsx';
import { useEffectsPresets } from '@/hooks/useVideoApi';
import type { DemoScene, CameraEffects } from './types';

interface EffectsPanelProps {
  scene: DemoScene | null;
  onEffectsChange?: (effects: CameraEffects) => void;
}

interface EffectConfig {
  id: keyof CameraEffects;
  label: string;
  description: string;
  defaultIntensity: number;
  min: number;
  max: number;
  step: number;
}

const EFFECT_CONFIGS: EffectConfig[] = [
  {
    id: 'vignette',
    label: 'Vignette',
    description: 'Darkens edges for focus',
    defaultIntensity: 0.4,
    min: 0,
    max: 1,
    step: 0.05,
  },
  {
    id: 'perspective_tilt',
    label: 'Perspective Tilt',
    description: 'Subtle 3D rotation effect',
    defaultIntensity: 0.3,
    min: 0,
    max: 1,
    step: 0.05,
  },
  {
    id: 'camera_shake',
    label: 'Camera Shake',
    description: 'Organic handheld motion',
    defaultIntensity: 0.2,
    min: 0,
    max: 0.5,
    step: 0.02,
  },
  {
    id: 'depth_of_field',
    label: 'Depth of Field',
    description: 'Blurred background effect',
    defaultIntensity: 0.3,
    min: 0,
    max: 1,
    step: 0.05,
  },
  {
    id: 'motion_blur',
    label: 'Motion Blur',
    description: 'Blur during camera moves',
    defaultIntensity: 0.2,
    min: 0,
    max: 0.5,
    step: 0.02,
  },
];

export function EffectsPanel({ scene, onEffectsChange }: EffectsPanelProps) {
  const { data: presetsData, isLoading: presetsLoading } = useEffectsPresets();

  // Local effects state
  const [selectedPreset, setSelectedPreset] = useState<string>('cinematic');
  const [effects, setEffects] = useState<CameraEffects>({
    vignette: { enabled: true, intensity: 0.4 },
    perspective_tilt: { enabled: true, intensity: 0.3 },
    camera_shake: { enabled: false, intensity: 0.2 },
    depth_of_field: { enabled: false, blur_amount: 0.3 },
    motion_blur: { enabled: false, intensity: 0.2 },
  });

  // Load from scene when it changes
  useEffect(() => {
    if (scene?.effects) {
      setEffects(scene.effects);
    }
  }, [scene]);

  const handlePresetChange = (presetId: string) => {
    setSelectedPreset(presetId);
    const preset = presetsData?.presets.find((p) => p.id === presetId);
    if (preset) {
      // Apply preset to effects
      const newEffects: CameraEffects = {
        vignette: {
          enabled: preset.vignette_enabled,
          intensity: preset.vignette_enabled ? 0.4 : 0,
        },
        perspective_tilt: {
          enabled: preset.perspective_enabled,
          intensity: preset.perspective_enabled ? 0.3 : 0,
        },
        camera_shake: {
          enabled: preset.shake_enabled,
          intensity: preset.shake_enabled ? 0.15 : 0,
        },
        depth_of_field: {
          enabled: preset.depth_of_field_enabled,
          blur_amount: preset.depth_of_field_enabled ? 0.3 : 0,
        },
        motion_blur: {
          enabled: preset.motion_blur_enabled,
          intensity: preset.motion_blur_enabled ? 0.2 : 0,
        },
      };
      setEffects(newEffects);
      onEffectsChange?.(newEffects);
    }
  };

  const toggleEffect = (effectId: keyof CameraEffects) => {
    const effect = effects[effectId];
    if (effect) {
      const newEffects = {
        ...effects,
        [effectId]: {
          ...effect,
          enabled: !effect.enabled,
        },
      };
      setEffects(newEffects);
      onEffectsChange?.(newEffects);
    }
  };

  const updateIntensity = (effectId: keyof CameraEffects, value: number) => {
    const effect = effects[effectId];
    if (effect) {
      const intensityKey = effectId === 'depth_of_field' ? 'blur_amount' : 'intensity';
      const newEffects = {
        ...effects,
        [effectId]: {
          ...effect,
          [intensityKey]: value,
        },
      };
      setEffects(newEffects);
      onEffectsChange?.(newEffects);
    }
  };

  const getIntensity = (effectId: keyof CameraEffects): number => {
    const effect = effects[effectId];
    if (!effect) return 0;
    if (effectId === 'depth_of_field') {
      return (effect as CameraEffects['depth_of_field'])?.blur_amount ?? 0;
    }
    return (effect as { intensity?: number })?.intensity ?? 0;
  };

  if (!scene) {
    return (
      <div className="p-4 text-center text-base-content/50">
        <Sparkles size={24} className="mx-auto mb-2 opacity-50" />
        <p className="text-sm">Select a scene to configure effects</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-base-content/70 uppercase tracking-wider flex items-center gap-2">
          <Sparkles size={14} />
          Effects
        </h3>
      </div>

      {/* Preset Dropdown */}
      <div>
        <label className="text-xs text-base-content/60 mb-1.5 block">Effects Preset</label>
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

      {/* Effect Toggles */}
      <div className="space-y-2">
        {EFFECT_CONFIGS.map((config) => {
          const effect = effects[config.id];
          const isEnabled = effect?.enabled ?? false;
          const intensity = getIntensity(config.id);

          return (
            <div
              key={config.id}
              className={clsx(
                'bg-base-300 rounded-lg p-3 transition-opacity',
                !isEnabled && 'opacity-60'
              )}
            >
              {/* Toggle Row */}
              <div className="flex items-center gap-3">
                <button
                  className={clsx(
                    'w-8 h-8 rounded-lg flex items-center justify-center transition-colors',
                    isEnabled
                      ? 'bg-primary/20 text-primary'
                      : 'bg-base-200 text-base-content/40'
                  )}
                  onClick={() => toggleEffect(config.id)}
                  title={isEnabled ? 'Disable' : 'Enable'}
                >
                  {isEnabled ? <Eye size={16} /> : <EyeOff size={16} />}
                </button>
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium">{config.label}</div>
                  <div className="text-xs text-base-content/50 truncate">
                    {config.description}
                  </div>
                </div>
                <div className="text-xs text-base-content/60 tabular-nums w-10 text-right">
                  {isEnabled ? intensity.toFixed(2) : 'off'}
                </div>
              </div>

              {/* Intensity Slider */}
              {isEnabled && (
                <div className="mt-2 pt-2 border-t border-base-200">
                  <input
                    type="range"
                    min={config.min}
                    max={config.max}
                    step={config.step}
                    value={intensity}
                    onChange={(e) => updateIntensity(config.id, parseFloat(e.target.value))}
                    className="range range-xs range-primary w-full"
                  />
                  <div className="flex justify-between text-[10px] text-base-content/40 mt-0.5">
                    <span>{config.min}</span>
                    <span>{config.max}</span>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Active Effects Summary */}
      <div className="pt-2 border-t border-base-300">
        <div className="text-xs text-base-content/50">
          {Object.values(effects).filter((e) => e?.enabled).length} of{' '}
          {EFFECT_CONFIGS.length} effects active
        </div>
      </div>
    </div>
  );
}
