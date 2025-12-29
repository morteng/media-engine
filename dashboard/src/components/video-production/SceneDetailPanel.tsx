/**
 * Scene Detail Panel
 *
 * Shows details for the currently selected scene with:
 * - Voiceover text
 * - Visual settings (background, transitions, effects)
 * - Scene notes with editing
 * - AI queue integration for feedback/improvements
 */

import { useState, useEffect } from 'react';
import {
  MessageSquare,
  Mic,
  Palette,
  Send,
  Loader2,
  Clock,
  CheckCircle,
  Wand2,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import clsx from 'clsx';

interface Scene {
  id: string;
  type: string;
  title?: string;
  text?: string;
  voiceover?: string;
  duration: number;
  startFrame: number;
  endFrame: number;
  background?: string;
  transition_in?: string;
  transition_out?: string;
  text_effect?: string;
  visual?: Record<string, unknown>;
}

interface SceneNote {
  text: string;
  created: string;
  scene_id: string;
}

interface SceneDetailPanelProps {
  scene: Scene | null;
  scriptPath: string | null;
  fps?: number;  // For future use in duration calculations
  onNoteChange?: (sceneId: string, note: string) => void;
  onSubmitToAI?: (sceneId: string, operation: string, instructions: string) => void;
  className?: string;
}

const AI_OPERATIONS = [
  { value: 'improve', label: 'Improve', description: 'Enhance clarity and flow' },
  { value: 'expand', label: 'Expand', description: 'Add more detail' },
  { value: 'simplify', label: 'Simplify', description: 'Make more concise' },
  { value: 'analyze', label: 'Analyze', description: 'Get feedback without changes' },
];

export function SceneDetailPanel({
  scene,
  scriptPath,
  onNoteChange,
  onSubmitToAI,
  className,
}: SceneDetailPanelProps) {
  const [note, setNote] = useState('');
  const [savedNote, setSavedNote] = useState<SceneNote | null>(null);
  const [isLoadingNote, setIsLoadingNote] = useState(false);
  const [isSavingNote, setIsSavingNote] = useState(false);
  const [noteSaved, setNoteSaved] = useState(false);

  const [showAIPanel, setShowAIPanel] = useState(false);
  const [aiOperation, setAiOperation] = useState('improve');
  const [aiInstructions, setAiInstructions] = useState('');
  const [isSubmittingAI, setIsSubmittingAI] = useState(false);
  const [aiSubmitted, setAiSubmitted] = useState(false);

  // Fetch existing note when scene changes
  useEffect(() => {
    if (!scene || !scriptPath) {
      setNote('');
      setSavedNote(null);
      return;
    }

    const fetchNote = async () => {
      setIsLoadingNote(true);
      try {
        const res = await fetch(`/api/scene-notes/${scriptPath}`);
        if (res.ok) {
          const data = await res.json();
          const sceneNote = data.notes?.[scene.id];
          if (sceneNote) {
            setSavedNote(sceneNote);
            setNote(sceneNote.text || '');
          } else {
            setSavedNote(null);
            setNote('');
          }
        }
      } catch {
        // Ignore errors
      } finally {
        setIsLoadingNote(false);
      }
    };

    fetchNote();
  }, [scene?.id, scriptPath]);

  // Save note with debounce
  useEffect(() => {
    if (!scene || !scriptPath || note === (savedNote?.text || '')) return;

    const timer = setTimeout(async () => {
      setIsSavingNote(true);
      try {
        const res = await fetch(`/api/scene-notes/${scriptPath}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ scene_id: scene.id, note }),
        });
        if (res.ok) {
          setSavedNote({ text: note, created: new Date().toISOString(), scene_id: scene.id });
          setNoteSaved(true);
          setTimeout(() => setNoteSaved(false), 2000);
          onNoteChange?.(scene.id, note);
        }
      } catch {
        // Ignore errors
      } finally {
        setIsSavingNote(false);
      }
    }, 1000);

    return () => clearTimeout(timer);
  }, [note, scene?.id, scriptPath, savedNote?.text, onNoteChange]);

  const handleSubmitToAI = async () => {
    if (!scene || !scriptPath) return;

    setIsSubmittingAI(true);
    try {
      const voiceoverText = scene.voiceover || scene.text || '';

      const res = await fetch('/api/ai/tasks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          operation: aiOperation,
          selections: [{
            path: scriptPath,
            content: voiceoverText,
            title: scene.title || `Scene: ${scene.id}`,
            content_type: 'video_scene',
            target_id: scene.id,
            notes: note ? [{ text: note, author: 'user' }] : [],
            metadata: {
              scene_id: scene.id,
              scene_type: scene.type,
              duration: scene.duration,
              background: scene.background,
              transition_in: scene.transition_in,
              text_effect: scene.text_effect,
            },
          }],
          instructions: aiInstructions || `${aiOperation} the voiceover for scene "${scene.title || scene.id}"`,
          priority: 'normal',
        }),
      });

      if (res.ok) {
        setAiSubmitted(true);
        setTimeout(() => setAiSubmitted(false), 3000);
        onSubmitToAI?.(scene.id, aiOperation, aiInstructions);
        setAiInstructions('');
      }
    } catch (error) {
      console.error('Failed to submit to AI:', error);
    } finally {
      setIsSubmittingAI(false);
    }
  };

  if (!scene) {
    return (
      <div className={clsx('card bg-base-200', className)}>
        <div className="card-body items-center justify-center text-center py-12">
          <MessageSquare size={32} className="text-base-content/30 mb-2" />
          <p className="text-base-content/60">Select a scene to view details</p>
        </div>
      </div>
    );
  }

  const voiceoverText = scene.voiceover || scene.text || '';
  const wordCount = voiceoverText.split(/\s+/).filter(Boolean).length;
  const estimatedDuration = Math.ceil(wordCount / 2.5); // ~150 wpm

  return (
    <div className={clsx('card bg-base-200 overflow-hidden', className)}>
      <div className="card-body p-4 space-y-4 overflow-y-auto">
        {/* Scene Header */}
        <div className="flex items-center gap-3">
          <div className={clsx(
            'w-3 h-3 rounded-full',
            scene.type === 'intro' ? 'bg-primary' :
            scene.type === 'outro' ? 'bg-success' :
            scene.type === 'demo' ? 'bg-accent' :
            scene.type === 'feature' ? 'bg-secondary' :
            'bg-base-content/30'
          )} />
          <div className="flex-1 min-w-0">
            <h4 className="font-semibold truncate">{scene.title || scene.id}</h4>
            <div className="text-xs text-base-content/60 flex items-center gap-2">
              <span className="badge badge-ghost badge-xs">{scene.type}</span>
              <span className="flex items-center gap-1">
                <Clock size={10} />
                {scene.duration}s
              </span>
            </div>
          </div>
        </div>

        {/* Voiceover Text */}
        <div className="space-y-2">
          <h5 className="text-sm font-medium flex items-center gap-2">
            <Mic size={14} className="text-primary" />
            Voiceover
            <span className="text-xs text-base-content/50 font-normal">
              ({wordCount} words, ~{estimatedDuration}s)
            </span>
          </h5>
          {voiceoverText ? (
            <div className="p-3 bg-base-300 rounded-lg text-sm leading-relaxed">
              {voiceoverText}
            </div>
          ) : (
            <p className="text-sm text-base-content/50 italic">No voiceover text</p>
          )}
        </div>

        {/* Visual Settings */}
        <div className="space-y-2">
          <h5 className="text-sm font-medium flex items-center gap-2">
            <Palette size={14} className="text-secondary" />
            Visual Settings
          </h5>
          <div className="grid grid-cols-2 gap-2 text-xs">
            {scene.background && (
              <div className="p-2 bg-base-300 rounded">
                <span className="text-base-content/50">Background:</span>
                <span className="ml-1 font-medium">{scene.background}</span>
              </div>
            )}
            {scene.transition_in && (
              <div className="p-2 bg-base-300 rounded">
                <span className="text-base-content/50">Transition:</span>
                <span className="ml-1 font-medium">{scene.transition_in}</span>
              </div>
            )}
            {scene.text_effect && (
              <div className="p-2 bg-base-300 rounded">
                <span className="text-base-content/50">Text Effect:</span>
                <span className="ml-1 font-medium">{scene.text_effect}</span>
              </div>
            )}
            {!scene.background && !scene.transition_in && !scene.text_effect && (
              <p className="text-base-content/50 italic col-span-2">Default settings</p>
            )}
          </div>
        </div>

        {/* Notes Section */}
        <div className="space-y-2">
          <h5 className="text-sm font-medium flex items-center gap-2">
            <MessageSquare size={14} className="text-warning" />
            Notes
            {isSavingNote && <Loader2 size={12} className="animate-spin text-base-content/50" />}
            {noteSaved && <CheckCircle size={12} className="text-success" />}
          </h5>
          <textarea
            className="textarea textarea-bordered w-full text-sm min-h-[80px] resize-none"
            placeholder="Add notes, feedback, or suggestions for this scene..."
            value={note}
            onChange={(e) => setNote(e.target.value)}
            disabled={isLoadingNote}
          />
        </div>

        {/* AI Queue Section */}
        <div className="space-y-2 border-t border-base-300 pt-4">
          <button
            onClick={() => setShowAIPanel(!showAIPanel)}
            className="w-full flex items-center gap-2 text-sm font-medium hover:text-primary transition-colors"
          >
            <Wand2 size={14} className="text-info" />
            Ask AI to Improve
            {showAIPanel ? <ChevronUp size={14} className="ml-auto" /> : <ChevronDown size={14} className="ml-auto" />}
            {aiSubmitted && <CheckCircle size={14} className="text-success" />}
          </button>

          {showAIPanel && (
            <div className="space-y-3 p-3 bg-base-300 rounded-lg">
              {/* Operation Selection */}
              <div className="flex flex-wrap gap-1">
                {AI_OPERATIONS.map((op) => (
                  <button
                    key={op.value}
                    onClick={() => setAiOperation(op.value)}
                    className={clsx(
                      'btn btn-xs',
                      aiOperation === op.value ? 'btn-primary' : 'btn-ghost'
                    )}
                    title={op.description}
                  >
                    {op.label}
                  </button>
                ))}
              </div>

              {/* Custom Instructions */}
              <textarea
                className="textarea textarea-bordered w-full text-sm min-h-[60px] resize-none"
                placeholder="Additional instructions for the AI (optional)..."
                value={aiInstructions}
                onChange={(e) => setAiInstructions(e.target.value)}
              />

              {/* Submit Button */}
              <button
                onClick={handleSubmitToAI}
                disabled={isSubmittingAI || !voiceoverText}
                className="btn btn-primary btn-sm w-full gap-2"
              >
                {isSubmittingAI ? (
                  <Loader2 size={14} className="animate-spin" />
                ) : (
                  <Send size={14} />
                )}
                Queue for AI Processing
              </button>

              {!voiceoverText && (
                <p className="text-xs text-warning text-center">
                  This scene has no voiceover text to process
                </p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default SceneDetailPanel;
