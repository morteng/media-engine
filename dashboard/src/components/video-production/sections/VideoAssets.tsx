/**
 * VideoAssets - Assets browser tab for video production
 * Displays demo clips, audio files, and motion components
 */

import {
  FileVideo,
  Mic,
  Package,
} from 'lucide-react';
import { Spinner } from '@/components/ui';
import { formatSize } from '@/utils/format';
import { useVideoAssets, useMotionComponents } from '@/hooks/useVideoApi';
import type { VideoAssetsResponse } from '@/api/types';

export function VideoAssets() {
  const { data: assetsData, isLoading } = useVideoAssets();
  const { data: componentsData } = useMotionComponents();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Spinner size="lg" className="text-primary" />
      </div>
    );
  }

  const assets: VideoAssetsResponse = assetsData || { demos: [], audio: [], graphics: [], outputs: [] };
  const components = componentsData || { components: [], backgrounds: [], transitions: [], text_effects: [] };

  return (
    <div className="space-y-6">
      {/* Demo Clips */}
      <div className="card bg-base-200">
        <div className="card-body">
          <h3 className="font-semibold flex items-center gap-2 mb-4">
            <FileVideo size={18} className="text-primary" />
            Demo Clips
            <span className="badge badge-ghost badge-sm">{assets.demos.length}</span>
          </h3>
          {assets.demos.length === 0 ? (
            <p className="text-base-content/60 text-sm">No demo clips captured</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {assets.demos.map((demo) => (
                <div key={demo.path} className="flex items-center gap-3 p-3 rounded-lg bg-base-300">
                  <FileVideo size={16} />
                  <div className="flex-1 min-w-0">
                    <div className="font-medium truncate text-sm">{demo.name}</div>
                    <div className="text-xs text-base-content/60">{formatSize(demo.size)}</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Audio Files */}
      <div className="card bg-base-200">
        <div className="card-body">
          <h3 className="font-semibold flex items-center gap-2 mb-4">
            <Mic size={18} className="text-success" />
            Voiceover Audio
            <span className="badge badge-ghost badge-sm">{assets.audio.length}</span>
          </h3>
          {assets.audio.length === 0 ? (
            <p className="text-base-content/60 text-sm">No voiceover files generated</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {assets.audio.map((audio) => (
                <div key={audio.path} className="flex items-center gap-3 p-3 rounded-lg bg-base-300">
                  <Mic size={16} />
                  <div className="flex-1 min-w-0">
                    <div className="font-medium truncate text-sm">{audio.name}</div>
                    <div className="text-xs text-base-content/60">
                      {audio.language} • {formatSize(audio.size)}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Motion Components */}
      <div className="card bg-base-200">
        <div className="card-body">
          <h3 className="font-semibold flex items-center gap-2 mb-4">
            <Package size={18} className="text-info" />
            Motion Graphics Components
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {components.components.map((comp: any) => (
              <div key={comp.id} className="p-3 rounded-lg bg-base-300">
                <div className="font-medium text-sm">{comp.name}</div>
                <div className="text-xs text-base-content/60 mt-1">{comp.description}</div>
                <div className="flex flex-wrap gap-1 mt-2">
                  {comp.props.slice(0, 3).map((prop: string) => (
                    <span key={prop} className="badge badge-ghost badge-xs">{prop}</span>
                  ))}
                </div>
              </div>
            ))}
          </div>

          {/* Quick reference */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6 pt-4 border-t border-base-300">
            <div>
              <h4 className="text-sm font-medium mb-2">Backgrounds</h4>
              <div className="flex flex-wrap gap-1">
                {components.backgrounds.map((bg: string) => (
                  <span key={bg} className="badge badge-primary badge-sm">{bg}</span>
                ))}
              </div>
            </div>
            <div>
              <h4 className="text-sm font-medium mb-2">Transitions</h4>
              <div className="flex flex-wrap gap-1">
                {components.transitions.slice(0, 8).map((t: string) => (
                  <span key={t} className="badge badge-secondary badge-sm">{t}</span>
                ))}
              </div>
            </div>
            <div>
              <h4 className="text-sm font-medium mb-2">Text Effects</h4>
              <div className="flex flex-wrap gap-1">
                {components.text_effects.map((e: string) => (
                  <span key={e} className="badge badge-accent badge-sm">{e}</span>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
