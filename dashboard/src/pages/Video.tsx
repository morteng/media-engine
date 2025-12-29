import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { MediaPlayer, Spinner } from '@/components/ui';
import { getDocuments, getFile, getSceneNotes, saveSceneNote } from '@/api/client';
import type { FileResponse } from '@/api/client';
import type { Document, VideoScene } from '@/api/types';
import {
  Film,
  Clock,
  MessageSquare,
  ChevronRight,
  Save,
  X,
  Mic,
  Eye,
  Layers,
  Play,
} from 'lucide-react';

interface SceneNote {
  text: string;
  created: string;
}

export function Video() {
  const [selectedScript, setSelectedScript] = useState<string | null>(null);
  const [selectedScene, setSelectedScene] = useState<string | null>(null);
  const [noteText, setNoteText] = useState('');
  const [editingNote, setEditingNote] = useState<string | null>(null);
  const queryClient = useQueryClient();

  // Fetch script documents
  const { data: docsData, isLoading: docsLoading } = useQuery({
    queryKey: ['documents', 'en'],
    queryFn: () => getDocuments('en'),
  });

  // Get script documents only
  const scripts = docsData?.categories?.script || [];

  // Fetch selected script content
  const { data: scriptData, isLoading: scriptLoading } = useQuery<FileResponse | null>({
    queryKey: ['file', selectedScript],
    queryFn: () => selectedScript ? getFile(selectedScript) : null,
    enabled: !!selectedScript,
  });

  const videoScript = scriptData?.parsed;
  const videoInfo = scriptData?.video;

  // Fetch scene notes for selected script
  const { data: notesData } = useQuery({
    queryKey: ['sceneNotes', selectedScript],
    queryFn: () => selectedScript ? getSceneNotes(selectedScript) : null,
    enabled: !!selectedScript,
  });

  const sceneNotes: Record<string, SceneNote> = notesData?.notes || {};

  // Save scene note mutation
  const saveNoteMutation = useMutation({
    mutationFn: ({ sceneId, note }: { sceneId: string; note: string }) =>
      saveSceneNote(selectedScript!, sceneId, note),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sceneNotes', selectedScript] });
      setEditingNote(null);
      setNoteText('');
    },
  });

  const handleSaveNote = (sceneId: string) => {
    saveNoteMutation.mutate({ sceneId, note: noteText });
  };

  const startEditingNote = (sceneId: string, existingNote?: string) => {
    setEditingNote(sceneId);
    setNoteText(existingNote || '');
  };

  const cancelEditing = () => {
    setEditingNote(null);
    setNoteText('');
  };

  const getTotalDuration = (scenes: VideoScene[]) => {
    return scenes.reduce((sum, scene) => sum + (scene.duration || 0), 0);
  };

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return mins > 0 ? `${mins}m ${secs}s` : `${secs}s`;
  };

  const getSceneTypeBadge = (type: string) => {
    const variants: Record<string, string> = {
      intro: 'badge-primary',
      feature: 'badge-info',
      demo: 'badge-success',
      outro: 'badge-warning',
      transition: 'badge-ghost',
    };
    return variants[type] || 'badge-ghost';
  };

  if (docsLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <Spinner size="lg" className="text-primary" />
          <p className="mt-4 text-base-content/60">Loading video scripts...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex gap-6 h-[calc(100vh-200px)]">
      {/* Sidebar - Script List */}
      <aside className="w-72 flex-shrink-0 flex flex-col bg-base-200 rounded-lg overflow-hidden">
        <div className="p-4 border-b border-base-300 flex items-center justify-between">
          <h3 className="font-semibold flex items-center gap-2">
            <Layers size={16} /> Scripts
          </h3>
          <div className="badge badge-ghost badge-sm">{scripts.length}</div>
        </div>

        {scripts.length === 0 ? (
          <div className="flex-1 flex items-center justify-center p-4">
            <p className="text-sm text-base-content/60">No video scripts found</p>
          </div>
        ) : (
          <nav className="flex-1 overflow-y-auto p-2 space-y-1">
            {scripts.map((doc: Document) => (
              <button
                key={doc.path}
                className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg text-left text-sm transition-colors ${
                  selectedScript === doc.path
                    ? 'bg-primary/20 text-primary'
                    : 'hover:bg-base-300 text-base-content/80'
                }`}
                onClick={() => {
                  setSelectedScript(doc.path);
                  setSelectedScene(null);
                }}
              >
                <Film size={14} />
                <span className="flex-1 truncate">{doc.title || doc.filename}</span>
                <ChevronRight size={14} className="text-base-content/40" />
              </button>
            ))}
          </nav>
        )}
      </aside>

      {/* Main Content - Scene Viewer */}
      <main className="flex-1 min-w-0 overflow-y-auto">
        {selectedScript ? (
          scriptLoading ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <Spinner size="md" className="text-primary" />
                <p className="mt-2 text-sm text-base-content/60">Loading script...</p>
              </div>
            </div>
          ) : videoScript ? (
            <div className="space-y-6">
              {/* Script Header */}
              <div className="card bg-base-200">
                <div className="card-body">
                  <h2 className="card-title text-xl">{videoScript.title}</h2>
                  <p className="text-base-content/60">{videoScript.description}</p>
                  <div className="flex flex-wrap gap-2 mt-2">
                    <div className="badge badge-info gap-1">
                      <Clock size={12} /> {formatDuration(getTotalDuration(videoScript.scenes || []))}
                    </div>
                    <div className="badge badge-ghost">
                      {videoScript.scenes?.length || 0} scenes
                    </div>
                    {videoScript.narrator && (
                      <div className="badge badge-ghost gap-1">
                        <Mic size={12} /> {videoScript.narrator.voice}
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Video/Audio Preview */}
              {(videoInfo?.hasVideo || videoInfo?.hasAudio) && (
                <div className="card bg-base-200">
                  <div className="card-body">
                    <h4 className="font-medium flex items-center gap-2 mb-3">
                      <Play size={14} /> Preview
                    </h4>
                    <MediaPlayer
                      src={videoInfo.videoUrl || videoInfo.audioUrl || ''}
                      type={videoInfo.hasVideo ? 'video' : 'audio'}
                      poster={undefined}
                      captions={videoInfo.captionsUrl}
                      title={videoScript.title}
                      sceneTiming={videoInfo.sceneTiming}
                      onSceneChange={(sceneId) => setSelectedScene(sceneId)}
                      className="rounded-lg overflow-hidden"
                    />
                  </div>
                </div>
              )}

              {/* Scenes */}
              <div className="space-y-3">
                <h4 className="font-semibold">Scenes</h4>
                {videoScript.scenes?.map((scene, index) => {
                  const hasNote = !!sceneNotes[scene.id];
                  const isEditing = editingNote === scene.id;
                  const isSelected = selectedScene === scene.id;

                  return (
                    <div
                      key={scene.id}
                      className={`card bg-base-200 cursor-pointer transition-all ${
                        isSelected ? 'ring-2 ring-primary' : 'hover:bg-base-300'
                      }`}
                      onClick={() => setSelectedScene(scene.id)}
                    >
                      <div className="card-body p-4">
                        <div className="flex items-start gap-3">
                          <div className="w-8 h-8 rounded-full bg-base-300 flex items-center justify-center text-sm font-semibold flex-shrink-0">
                            {index + 1}
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-1">
                              <span className="font-medium">{scene.name || scene.id}</span>
                              <div className={`badge badge-sm ${getSceneTypeBadge(scene.type)}`}>
                                {scene.type}
                              </div>
                            </div>
                            <div className="flex items-center gap-2 text-sm text-base-content/60">
                              <Clock size={12} /> {formatDuration(scene.duration)}
                            </div>
                          </div>
                          {hasNote && !isEditing && (
                            <MessageSquare size={16} className="text-primary flex-shrink-0" />
                          )}
                        </div>

                        {scene.voiceover && (
                          <div className="flex items-start gap-2 mt-3 p-2 rounded bg-base-300 text-sm">
                            <Mic size={14} className="text-primary flex-shrink-0 mt-0.5" />
                            <p className="text-base-content/80">{scene.voiceover}</p>
                          </div>
                        )}

                        {scene.visual && (
                          <div className="flex items-center gap-2 mt-2 text-sm text-base-content/60">
                            <Eye size={14} />
                            <span>
                              {scene.visual.background ? `Background: ${scene.visual.background as string}` : ''}
                              {scene.visual.transition_in ? ` | Transition: ${scene.visual.transition_in as string}` : ''}
                            </span>
                          </div>
                        )}

                        {/* Note Display/Editor */}
                        <div className="mt-3 pt-3 border-t border-base-300">
                          {isEditing ? (
                            <div className="space-y-2" onClick={(e) => e.stopPropagation()}>
                              <textarea
                                className="textarea textarea-bordered w-full text-sm"
                                value={noteText}
                                onChange={(e) => setNoteText(e.target.value)}
                                placeholder="Add a note or comment for this scene..."
                                rows={3}
                              />
                              <div className="flex gap-2">
                                <button
                                  className="btn btn-primary btn-sm gap-1"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handleSaveNote(scene.id);
                                  }}
                                  disabled={saveNoteMutation.isPending}
                                >
                                  <Save size={14} /> Save
                                </button>
                                <button
                                  className="btn btn-ghost btn-sm gap-1"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    cancelEditing();
                                  }}
                                >
                                  <X size={14} /> Cancel
                                </button>
                              </div>
                            </div>
                          ) : hasNote ? (
                            <div
                              className="p-2 rounded bg-primary/10 cursor-pointer hover:bg-primary/20 transition-colors"
                              onClick={(e) => {
                                e.stopPropagation();
                                startEditingNote(scene.id, sceneNotes[scene.id].text);
                              }}
                            >
                              <div className="flex items-start gap-2">
                                <MessageSquare size={14} className="text-primary flex-shrink-0 mt-0.5" />
                                <div className="flex-1 min-w-0">
                                  <p className="text-sm">{sceneNotes[scene.id].text}</p>
                                  <span className="text-xs text-base-content/50">
                                    {new Date(sceneNotes[scene.id].created).toLocaleDateString()}
                                  </span>
                                </div>
                              </div>
                            </div>
                          ) : (
                            <button
                              className="btn btn-ghost btn-sm gap-1 text-base-content/60"
                              onClick={(e) => {
                                e.stopPropagation();
                                startEditingNote(scene.id);
                              }}
                            >
                              <MessageSquare size={14} /> Add Note
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <Film size={48} className="text-base-content/30 mb-4" />
              <p className="text-base-content/60">Could not parse script</p>
            </div>
          )
        ) : scripts.length > 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <Film size={48} className="text-base-content/30 mb-4" />
            <h3 className="text-lg font-semibold">Select a Script</h3>
            <p className="text-base-content/60">Choose a video script from the list to view scenes and manage notes</p>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <Film size={48} className="text-base-content/30 mb-4" />
            <h3 className="text-lg font-semibold">No Scripts Found</h3>
            <p className="text-base-content/60">Add video scripts to your content directory to get started</p>
          </div>
        )}
      </main>
    </div>
  );
}
