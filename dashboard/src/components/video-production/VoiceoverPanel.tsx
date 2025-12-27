import { useState } from 'react';
import { Play, Pause, Volume2, Mic, RefreshCw } from 'lucide-react';
import { useQuery, useMutation } from '@tanstack/react-query';
import api from '../../api/client';

interface Voice {
  id: string;
  name: string;
  language: string;
  gender: 'male' | 'female' | 'neutral';
  style: string;
  preview_url?: string;
}

interface VoiceoverPanelProps {
  scriptId?: string;
  sceneId?: string;
  text?: string;
  className?: string;
}

const MOCK_VOICES: Voice[] = [
  { id: 'en-US-Neural2-A', name: 'Alex', language: 'en-US', gender: 'male', style: 'professional' },
  { id: 'en-US-Neural2-C', name: 'Sarah', language: 'en-US', gender: 'female', style: 'professional' },
  { id: 'en-US-Neural2-D', name: 'Michael', language: 'en-US', gender: 'male', style: 'casual' },
  { id: 'en-US-Neural2-E', name: 'Emma', language: 'en-US', gender: 'female', style: 'casual' },
  { id: 'en-GB-Neural2-A', name: 'James', language: 'en-GB', gender: 'male', style: 'professional' },
  { id: 'en-GB-Neural2-C', name: 'Sophie', language: 'en-GB', gender: 'female', style: 'professional' },
];

export function VoiceoverPanel({ text = '', className = '' }: VoiceoverPanelProps) {
  const [selectedVoice, setSelectedVoice] = useState<Voice>(MOCK_VOICES[0]);
  const [isPlaying, setIsPlaying] = useState(false);
  const [previewText, setPreviewText] = useState(text);
  const [speed, setSpeed] = useState(1.0);
  const [pitch, setPitch] = useState(1.0);

  // Fetch available voices
  const { data: voices } = useQuery({
    queryKey: ['video', 'voices'],
    queryFn: async () => {
      try {
        const response = await api.get('/api/video/voices');
        return response.data.voices as Voice[];
      } catch {
        return MOCK_VOICES;
      }
    },
    staleTime: 60000,
  });

  // Preview voiceover mutation
  const previewMutation = useMutation({
    mutationFn: async (params: { text: string; voice_id: string; speed: number; pitch: number }) => {
      const response = await api.post('/api/video/voiceover/preview', params);
      return response.data;
    },
    onSuccess: (data) => {
      if (data.audio_url) {
        const audio = new Audio(data.audio_url);
        audio.onended = () => setIsPlaying(false);
        audio.play();
        setIsPlaying(true);
      }
    },
  });

  const handlePreview = () => {
    if (isPlaying) {
      setIsPlaying(false);
      return;
    }

    if (!previewText.trim()) return;

    previewMutation.mutate({
      text: previewText,
      voice_id: selectedVoice.id,
      speed,
      pitch,
    });
  };

  const estimatedDuration = (previewText.split(/\s+/).length / 150) * 60 / speed;

  const voiceList = voices || MOCK_VOICES;

  return (
    <div className={`flex flex-col h-full ${className}`}>
      {/* Voice selection */}
      <div className="p-4 border-b border-base-300">
        <h3 className="font-medium mb-3 flex items-center gap-2">
          <Mic className="h-4 w-4" />
          Voice Selection
        </h3>

        <div className="grid grid-cols-2 gap-2">
          {voiceList.map((voice) => (
            <button
              key={voice.id}
              className={`btn btn-sm ${
                selectedVoice.id === voice.id ? 'btn-primary' : 'btn-ghost'
              } justify-start`}
              onClick={() => setSelectedVoice(voice)}
            >
              <div className="flex flex-col items-start">
                <span className="font-medium">{voice.name}</span>
                <span className="text-xs opacity-70">
                  {voice.language} • {voice.gender}
                </span>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Voice settings */}
      <div className="p-4 border-b border-base-300 space-y-3">
        <div>
          <label className="label">
            <span className="label-text text-xs">Speed: {speed.toFixed(1)}x</span>
          </label>
          <input
            type="range"
            min="0.5"
            max="2"
            step="0.1"
            value={speed}
            onChange={(e) => setSpeed(parseFloat(e.target.value))}
            className="range range-xs range-primary"
          />
        </div>

        <div>
          <label className="label">
            <span className="label-text text-xs">Pitch: {pitch.toFixed(1)}</span>
          </label>
          <input
            type="range"
            min="0.5"
            max="1.5"
            step="0.1"
            value={pitch}
            onChange={(e) => setPitch(parseFloat(e.target.value))}
            className="range range-xs range-primary"
          />
        </div>
      </div>

      {/* Preview text */}
      <div className="flex-1 p-4 overflow-auto">
        <label className="label">
          <span className="label-text text-xs">Preview Text</span>
          <span className="label-text-alt text-xs">
            ~{estimatedDuration.toFixed(1)}s • {previewText.split(/\s+/).filter(Boolean).length} words
          </span>
        </label>
        <textarea
          className="textarea textarea-bordered w-full h-32 text-sm"
          placeholder="Enter text to preview voiceover..."
          value={previewText}
          onChange={(e) => setPreviewText(e.target.value)}
        />
      </div>

      {/* Preview controls */}
      <div className="p-4 border-t border-base-300">
        <div className="flex items-center gap-2">
          <button
            className={`btn btn-primary flex-1 ${previewMutation.isPending ? 'loading' : ''}`}
            onClick={handlePreview}
            disabled={!previewText.trim() || previewMutation.isPending}
          >
            {isPlaying ? (
              <>
                <Pause className="h-4 w-4" />
                Stop
              </>
            ) : (
              <>
                <Play className="h-4 w-4" />
                Preview
              </>
            )}
          </button>

          <button
            className="btn btn-ghost btn-square"
            onClick={() => setPreviewText(text)}
            title="Reset to original"
          >
            <RefreshCw className="h-4 w-4" />
          </button>

          <div className="flex items-center gap-1 text-base-content/60">
            <Volume2 className="h-4 w-4" />
          </div>
        </div>

        {previewMutation.isError && (
          <div className="alert alert-error mt-2 py-2">
            <span className="text-xs">Preview not available. TTS service may be offline.</span>
          </div>
        )}
      </div>
    </div>
  );
}
