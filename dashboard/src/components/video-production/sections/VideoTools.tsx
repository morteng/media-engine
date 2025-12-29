/**
 * VideoTools - Tools tab for video production
 * Provides component library and voiceover preview
 */

import { Package, Mic } from 'lucide-react';
import { ComponentLibrary, VoiceoverPanel } from '@/components/video-production';

export function VideoTools() {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-[calc(100vh-280px)]">
      {/* Component Library */}
      <div className="card bg-base-200 overflow-hidden">
        <div className="card-body p-0 flex flex-col h-full">
          <div className="p-4 border-b border-base-300">
            <h3 className="font-semibold flex items-center gap-2">
              <Package size={16} />
              Component Library
            </h3>
            <p className="text-xs text-base-content/60 mt-1">
              Browse motion graphics components for your videos
            </p>
          </div>
          <ComponentLibrary
            className="flex-1"
            onSelectComponent={(comp) => {
              // Could be used to insert component into script
              console.log('Selected component:', comp);
            }}
          />
        </div>
      </div>

      {/* Voiceover Panel */}
      <div className="card bg-base-200 overflow-hidden">
        <div className="card-body p-0 flex flex-col h-full">
          <div className="p-4 border-b border-base-300">
            <h3 className="font-semibold flex items-center gap-2">
              <Mic size={16} />
              Voiceover Preview
            </h3>
            <p className="text-xs text-base-content/60 mt-1">
              Preview and configure text-to-speech voiceovers
            </p>
          </div>
          <VoiceoverPanel className="flex-1" />
        </div>
      </div>
    </div>
  );
}
