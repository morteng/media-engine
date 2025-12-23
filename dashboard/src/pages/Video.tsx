import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Badge, Spinner, MediaPlayer } from '@/components/ui';
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
import clsx from 'clsx';
import './Video.css';

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

  const getSceneTypeColor = (type: string): 'default' | 'info' | 'success' | 'warning' | 'error' | 'accent' => {
    const colors: Record<string, 'default' | 'info' | 'success' | 'warning' | 'error' | 'accent'> = {
      intro: 'accent',
      feature: 'info',
      demo: 'success',
      outro: 'warning',
      transition: 'default',
    };
    return colors[type] || 'default';
  };

  if (docsLoading) {
    return (
      <div className="video-loading">
        <Spinner size="lg" />
        <p>Loading video scripts...</p>
      </div>
    );
  }

  return (
    <div className="video-layout">
      {/* Sidebar - Script List */}
      <aside className="video-sidebar">
        <div className="video-sidebar-header">
          <h3><Layers size={16} /> Scripts</h3>
          <Badge variant="default" size="sm">{scripts.length}</Badge>
        </div>

        {scripts.length === 0 ? (
          <div className="video-empty-sidebar">
            <p>No video scripts found</p>
          </div>
        ) : (
          <nav className="script-list">
            {scripts.map((doc: Document) => (
              <button
                key={doc.path}
                className={clsx('script-item', { active: selectedScript === doc.path })}
                onClick={() => {
                  setSelectedScript(doc.path);
                  setSelectedScene(null);
                }}
              >
                <Film size={14} />
                <span className="script-title">{doc.title || doc.filename}</span>
                <ChevronRight size={14} className="chevron" />
              </button>
            ))}
          </nav>
        )}
      </aside>

      {/* Main Content - Scene Viewer */}
      <main className="video-main">
        {selectedScript ? (
          scriptLoading ? (
            <div className="video-loading">
              <Spinner />
              <p>Loading script...</p>
            </div>
          ) : videoScript ? (
            <div className="script-content">
              {/* Script Header */}
              <header className="script-header">
                <h2>{videoScript.title}</h2>
                <p className="script-description">{videoScript.description}</p>
                <div className="script-meta">
                  <Badge variant="info">
                    <Clock size={12} /> {formatDuration(getTotalDuration(videoScript.scenes || []))}
                  </Badge>
                  <Badge variant="default">
                    {videoScript.scenes?.length || 0} scenes
                  </Badge>
                  {videoScript.narrator && (
                    <Badge variant="default">
                      <Mic size={12} /> {videoScript.narrator.voice}
                    </Badge>
                  )}
                </div>
              </header>

              {/* Video/Audio Preview */}
              {(videoInfo?.hasVideo || videoInfo?.hasAudio) && (
                <section className="video-preview-section">
                  <h4><Play size={14} /> Preview</h4>
                  <MediaPlayer
                    src={videoInfo.videoUrl || videoInfo.audioUrl || ''}
                    type={videoInfo.hasVideo ? 'video' : 'audio'}
                    poster={undefined}
                    captions={videoInfo.captionsUrl}
                    title={videoScript.title}
                    sceneTiming={videoInfo.sceneTiming}
                    onSceneChange={(sceneId) => setSelectedScene(sceneId)}
                    className="script-media-player"
                  />
                </section>
              )}

              {/* Scenes */}
              <section className="scenes-section">
                <h4>Scenes</h4>
                <div className="scenes-list">
                  {videoScript.scenes?.map((scene, index) => {
                    const hasNote = !!sceneNotes[scene.id];
                    const isEditing = editingNote === scene.id;
                    const isSelected = selectedScene === scene.id;

                    return (
                      <div
                        key={scene.id}
                        className={clsx('scene-card', { selected: isSelected })}
                        onClick={() => setSelectedScene(scene.id)}
                      >
                        <div className="scene-header">
                          <div className="scene-number">{index + 1}</div>
                          <div className="scene-info">
                            <div className="scene-title">
                              <span>{scene.name || scene.id}</span>
                              <Badge variant={getSceneTypeColor(scene.type)} size="sm">
                                {scene.type}
                              </Badge>
                            </div>
                            <div className="scene-meta">
                              <span><Clock size={12} /> {formatDuration(scene.duration)}</span>
                            </div>
                          </div>
                          {hasNote && !isEditing && (
                            <MessageSquare size={16} className="has-note-icon" />
                          )}
                        </div>

                        {scene.voiceover && (
                          <div className="scene-voiceover">
                            <Mic size={14} />
                            <p>{scene.voiceover}</p>
                          </div>
                        )}

                        {scene.visual && (
                          <div className="scene-visual">
                            <Eye size={14} />
                            <span>
                              {scene.visual.background ? `Background: ${scene.visual.background as string}` : ''}
                              {scene.visual.transition_in ? ` | Transition: ${scene.visual.transition_in as string}` : ''}
                            </span>
                          </div>
                        )}

                        {/* Note Display/Editor */}
                        <div className="scene-note-section">
                          {isEditing ? (
                            <div className="note-editor">
                              <textarea
                                value={noteText}
                                onChange={(e) => setNoteText(e.target.value)}
                                placeholder="Add a note or comment for this scene..."
                                rows={3}
                                onClick={(e) => e.stopPropagation()}
                              />
                              <div className="note-actions">
                                <button
                                  className="btn btn-primary btn-sm"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handleSaveNote(scene.id);
                                  }}
                                  disabled={saveNoteMutation.isPending}
                                >
                                  <Save size={14} /> Save
                                </button>
                                <button
                                  className="btn btn-ghost btn-sm"
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
                              className="note-display"
                              onClick={(e) => {
                                e.stopPropagation();
                                startEditingNote(scene.id, sceneNotes[scene.id].text);
                              }}
                            >
                              <MessageSquare size={14} />
                              <p>{sceneNotes[scene.id].text}</p>
                              <span className="note-date">
                                {new Date(sceneNotes[scene.id].created).toLocaleDateString()}
                              </span>
                            </div>
                          ) : (
                            <button
                              className="add-note-btn"
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
                    );
                  })}
                </div>
              </section>
            </div>
          ) : (
            <div className="video-empty-state">
              <Film size={48} />
              <p>Could not parse script</p>
            </div>
          )
        ) : scripts.length > 0 ? (
          <div className="video-empty-state">
            <Film size={48} />
            <h3>Select a Script</h3>
            <p>Choose a video script from the list to view scenes and manage notes</p>
          </div>
        ) : (
          <div className="video-empty-state">
            <Film size={48} />
            <h3>No Scripts Found</h3>
            <p>Add video scripts to your content directory to get started</p>
          </div>
        )}
      </main>
    </div>
  );
}
