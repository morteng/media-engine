import { useState } from 'react';
import { Play, Volume2, Mic, RefreshCw, Check, AlertCircle, Loader2, Clock } from 'lucide-react';
import { useVoiceoverStatus, useGenerateVoiceover } from '@/hooks/useVideoApi';
import type { VoiceoverMode } from '@/api/video';

interface VoiceoverPanelProps {
  scriptId?: string | null;
  className?: string;
  onGenerated?: () => void;
}

// Available TTS modes with descriptions
const VOICEOVER_MODES: { id: VoiceoverMode; name: string; description: string; icon: string }[] = [
  { id: 'mock', name: 'Mock (Silent)', description: 'Generate timing-only audio for testing', icon: '🔇' },
  { id: 'macos', name: 'macOS TTS', description: 'Use built-in macOS text-to-speech', icon: '🍎' },
  { id: 'elevenlabs', name: 'ElevenLabs', description: 'High-quality AI voiceover (requires API key)', icon: '🎙️' },
];

export function VoiceoverPanel({ scriptId, className = '', onGenerated }: VoiceoverPanelProps) {
  const [selectedMode, setSelectedMode] = useState<VoiceoverMode>('mock');
  const [forceRegenerate, setForceRegenerate] = useState(false);

  // Fetch voiceover status
  const { data: status, isLoading: statusLoading, refetch: refetchStatus } = useVoiceoverStatus(scriptId ?? null);

  // Generate voiceover mutation
  const generateMutation = useGenerateVoiceover();

  const handleGenerate = () => {
    if (!scriptId) return;

    generateMutation.mutate(
      {
        scriptId,
        mode: selectedMode,
        force: forceRegenerate,
      },
      {
        onSuccess: () => {
          refetchStatus();
          onGenerated?.();
        },
      }
    );
  };

  // Format file size
  const formatSize = (bytes: number | null | undefined) => {
    if (!bytes) return 'Unknown size';
    const kb = bytes / 1024;
    if (kb < 1024) return `${kb.toFixed(1)} KB`;
    return `${(kb / 1024).toFixed(2)} MB`;
  };

  // Format date
  const formatDate = (dateStr: string | null | undefined) => {
    if (!dateStr) return 'Unknown';
    return new Date(dateStr).toLocaleString();
  };

  if (!scriptId) {
    return (
      <div className={`flex flex-col items-center justify-center h-full text-base-content/50 ${className}`}>
        <Mic className="h-12 w-12 mb-4 opacity-30" />
        <p>Select a script to manage voiceover</p>
      </div>
    );
  }

  return (
    <div className={`flex flex-col h-full ${className}`}>
      {/* Current Status */}
      <div className="p-4 border-b border-base-300">
        <h3 className="font-medium mb-3 flex items-center gap-2">
          <Volume2 className="h-4 w-4" />
          Voiceover Status
        </h3>

        {statusLoading ? (
          <div className="flex items-center gap-2 text-base-content/60">
            <Loader2 className="h-4 w-4 animate-spin" />
            Checking status...
          </div>
        ) : status?.has_voiceover ? (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-success">
              <Check className="h-4 w-4" />
              <span className="font-medium">Voiceover exists</span>
            </div>
            <div className="text-sm text-base-content/70 space-y-1">
              <div className="flex items-center gap-2">
                <Clock className="h-3 w-3" />
                <span>Modified: {formatDate(status.audio_modified)}</span>
              </div>
              <div>Size: {formatSize(status.audio_size)}</div>
              {status.has_props && (
                <div className="badge badge-sm badge-success gap-1">
                  <Check className="h-3 w-3" />
                  Props generated
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="flex items-center gap-2 text-warning">
            <AlertCircle className="h-4 w-4" />
            <span>No voiceover generated yet</span>
          </div>
        )}
      </div>

      {/* Mode Selection */}
      <div className="p-4 border-b border-base-300">
        <h3 className="font-medium mb-3 flex items-center gap-2">
          <Mic className="h-4 w-4" />
          Generation Mode
        </h3>

        <div className="space-y-2">
          {VOICEOVER_MODES.map((mode) => (
            <label
              key={mode.id}
              className={`flex items-start gap-3 p-3 rounded-lg cursor-pointer transition-colors ${
                selectedMode === mode.id
                  ? 'bg-primary/10 border border-primary'
                  : 'bg-base-200 hover:bg-base-300 border border-transparent'
              }`}
            >
              <input
                type="radio"
                name="voiceover-mode"
                value={mode.id}
                checked={selectedMode === mode.id}
                onChange={(e) => setSelectedMode(e.target.value as VoiceoverMode)}
                className="radio radio-primary radio-sm mt-0.5"
              />
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span>{mode.icon}</span>
                  <span className="font-medium">{mode.name}</span>
                </div>
                <p className="text-xs text-base-content/60 mt-0.5">{mode.description}</p>
              </div>
            </label>
          ))}
        </div>
      </div>

      {/* Options */}
      <div className="p-4 border-b border-base-300">
        <label className="flex items-center gap-3 cursor-pointer">
          <input
            type="checkbox"
            checked={forceRegenerate}
            onChange={(e) => setForceRegenerate(e.target.checked)}
            className="checkbox checkbox-sm checkbox-primary"
          />
          <div>
            <span className="font-medium text-sm">Force regenerate</span>
            <p className="text-xs text-base-content/60">
              Regenerate even if voiceover already exists
            </p>
          </div>
        </label>
      </div>

      {/* Generate Button */}
      <div className="p-4 mt-auto">
        <button
          className={`btn btn-primary w-full ${generateMutation.isPending ? 'loading' : ''}`}
          onClick={handleGenerate}
          disabled={generateMutation.isPending}
        >
          {generateMutation.isPending ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Generating...
            </>
          ) : status?.has_voiceover && !forceRegenerate ? (
            <>
              <RefreshCw className="h-4 w-4" />
              Regenerate Voiceover
            </>
          ) : (
            <>
              <Play className="h-4 w-4" />
              Generate Voiceover
            </>
          )}
        </button>

        {generateMutation.isError && (
          <div className="alert alert-error mt-3 py-2">
            <AlertCircle className="h-4 w-4" />
            <span className="text-sm">
              Failed to generate voiceover. Check console for details.
            </span>
          </div>
        )}

        {generateMutation.isSuccess && (
          <div className="alert alert-success mt-3 py-2">
            <Check className="h-4 w-4" />
            <span className="text-sm">
              {generateMutation.data.status === 'generating'
                ? 'Voiceover generation started in background'
                : 'Voiceover already exists'}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
