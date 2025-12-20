import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, Badge, Spinner } from '@/components/ui';
import { getDocuments, getFile, getSceneNotes, saveSceneNote } from '@/api/client';
import type { Document, VideoScript, VideoScene } from '@/api/types';
import {
  Film,
  Clock,
  MessageSquare,
  ChevronRight,
  Save,
  X,
  Mic,
  Eye,
  Layers
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
  const { data: scriptData, isLoading: scriptLoading } = useQuery({
    queryKey: ['file', selectedScript],
    queryFn: () => selectedScript ? getFile(selectedScript) : null,
    enabled: !!selectedScript,
  });

  const videoScript = scriptData?.parsed as VideoScript | undefined;

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
      <div className="page-loading">
        <Spinner size="lg" />
        <p>Loading video scripts...</p>
      </div>
    );
  }

  return (
    <div className="video-page">
      <header className="page-header">
        <div>
          <h1><Film size={24} /> Video Scripts</h1>
          <p className="text-secondary">Manage video scripts and scene notes</p>
        </div>
      </header>

      <div className="video-layout">
        {/* Script List */}
        <Card className="script-list">
          <h3><Layers size={18} /> Scripts ({scripts.length})</h3>
          {scripts.length === 0 ? (
            <p className="empty-state">No video scripts found</p>
          ) : (
            <ul className="script-items">
              {scripts.map((doc: Document) => (
                <li
                  key={doc.path}
                  className={`script-item ${selectedScript === doc.path ? 'active' : ''}`}
                  onClick={() => {
                    setSelectedScript(doc.path);
                    setSelectedScene(null);
                  }}
                >
                  <Film size={16} />
                  <span className="script-title">{doc.title || doc.filename}</span>
                  <ChevronRight size={14} className="chevron" />
                </li>
              ))}
            </ul>
          )}
        </Card>

        {/* Scene List */}
        {selectedScript && (
          <Card className="scene-list">
            {scriptLoading ? (
              <div className="loading-state">
                <Spinner />
                <p>Loading script...</p>
              </div>
            ) : videoScript ? (
              <>
                <div className="script-header">
                  <h3>{videoScript.title}</h3>
                  <p className="text-secondary">{videoScript.description}</p>
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
                </div>

                <div className="scenes-container">
                  <h4>Scenes</h4>
                  {videoScript.scenes?.map((scene, index) => {
                    const hasNote = !!sceneNotes[scene.id];
                    const isEditing = editingNote === scene.id;
                    const isSelected = selectedScene === scene.id;

                    return (
                      <div
                        key={scene.id}
                        className={`scene-card ${isSelected ? 'selected' : ''}`}
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
                                  className="btn btn-sm btn-primary"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handleSaveNote(scene.id);
                                  }}
                                  disabled={saveNoteMutation.isPending}
                                >
                                  <Save size={14} /> Save
                                </button>
                                <button
                                  className="btn btn-sm btn-secondary"
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
              </>
            ) : (
              <p className="empty-state">Could not parse script</p>
            )}
          </Card>
        )}

        {/* Empty State */}
        {!selectedScript && scripts.length > 0 && (
          <Card className="empty-selection">
            <Film size={48} className="empty-icon" />
            <h3>Select a Script</h3>
            <p>Choose a video script from the list to view scenes and manage notes</p>
          </Card>
        )}
      </div>

      <style>{`
        .video-page {
          padding: 1.5rem;
        }

        .page-header {
          margin-bottom: 1.5rem;
        }

        .page-header h1 {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          margin: 0 0 0.25rem 0;
        }

        .video-layout {
          display: grid;
          grid-template-columns: 280px 1fr;
          gap: 1.5rem;
          min-height: calc(100vh - 200px);
        }

        .script-list h3,
        .scene-list h3 {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          margin: 0 0 1rem 0;
          font-size: 1rem;
        }

        .script-items {
          list-style: none;
          padding: 0;
          margin: 0;
        }

        .script-item {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          padding: 0.75rem;
          border-radius: 0.5rem;
          cursor: pointer;
          transition: all 0.15s ease;
        }

        .script-item:hover {
          background: var(--bg-tertiary);
        }

        .script-item.active {
          background: var(--primary);
          color: white;
        }

        .script-item .script-title {
          flex: 1;
          font-size: 0.875rem;
        }

        .script-item .chevron {
          opacity: 0.5;
        }

        .script-header {
          margin-bottom: 1.5rem;
          padding-bottom: 1rem;
          border-bottom: 1px solid var(--border);
        }

        .script-header h3 {
          margin: 0 0 0.5rem 0;
        }

        .script-meta {
          display: flex;
          gap: 0.5rem;
          margin-top: 0.75rem;
          flex-wrap: wrap;
        }

        .scenes-container h4 {
          margin: 0 0 1rem 0;
          font-size: 0.875rem;
          color: var(--text-secondary);
          text-transform: uppercase;
          letter-spacing: 0.05em;
        }

        .scene-card {
          background: var(--bg-tertiary);
          border-radius: 0.75rem;
          padding: 1rem;
          margin-bottom: 1rem;
          cursor: pointer;
          transition: all 0.15s ease;
          border: 2px solid transparent;
        }

        .scene-card:hover {
          border-color: var(--border);
        }

        .scene-card.selected {
          border-color: var(--primary);
        }

        .scene-header {
          display: flex;
          align-items: flex-start;
          gap: 0.75rem;
        }

        .scene-number {
          width: 28px;
          height: 28px;
          background: var(--primary);
          color: white;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 0.75rem;
          font-weight: 600;
          flex-shrink: 0;
        }

        .scene-info {
          flex: 1;
        }

        .scene-title {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          font-weight: 500;
        }

        .scene-meta {
          display: flex;
          gap: 1rem;
          margin-top: 0.25rem;
          font-size: 0.75rem;
          color: var(--text-secondary);
        }

        .scene-meta span {
          display: flex;
          align-items: center;
          gap: 0.25rem;
        }

        .has-note-icon {
          color: var(--warning);
        }

        .scene-voiceover {
          display: flex;
          gap: 0.5rem;
          margin-top: 0.75rem;
          padding: 0.75rem;
          background: var(--bg-secondary);
          border-radius: 0.5rem;
          font-size: 0.875rem;
          color: var(--text-secondary);
        }

        .scene-voiceover svg {
          flex-shrink: 0;
          margin-top: 2px;
          color: var(--primary);
        }

        .scene-voiceover p {
          margin: 0;
          line-height: 1.5;
        }

        .scene-visual {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          margin-top: 0.5rem;
          font-size: 0.75rem;
          color: var(--text-tertiary);
        }

        .scene-note-section {
          margin-top: 0.75rem;
        }

        .note-editor textarea {
          width: 100%;
          padding: 0.75rem;
          border: 1px solid var(--border);
          border-radius: 0.5rem;
          background: var(--bg-secondary);
          color: var(--text-primary);
          font-size: 0.875rem;
          resize: vertical;
          font-family: inherit;
        }

        .note-editor textarea:focus {
          outline: none;
          border-color: var(--primary);
        }

        .note-actions {
          display: flex;
          gap: 0.5rem;
          margin-top: 0.5rem;
        }

        .btn {
          display: inline-flex;
          align-items: center;
          gap: 0.375rem;
          padding: 0.5rem 1rem;
          border-radius: 0.375rem;
          font-size: 0.875rem;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.15s ease;
          border: none;
        }

        .btn-sm {
          padding: 0.375rem 0.75rem;
          font-size: 0.75rem;
        }

        .btn-primary {
          background: var(--primary);
          color: white;
        }

        .btn-primary:hover {
          opacity: 0.9;
        }

        .btn-secondary {
          background: var(--bg-tertiary);
          color: var(--text-primary);
          border: 1px solid var(--border);
        }

        .btn-secondary:hover {
          background: var(--bg-secondary);
        }

        .note-display {
          display: flex;
          gap: 0.5rem;
          padding: 0.75rem;
          background: var(--warning-bg, rgba(251, 191, 36, 0.1));
          border-radius: 0.5rem;
          border: 1px solid var(--warning);
          cursor: pointer;
        }

        .note-display svg {
          flex-shrink: 0;
          color: var(--warning);
        }

        .note-display p {
          flex: 1;
          margin: 0;
          font-size: 0.875rem;
        }

        .note-display .note-date {
          font-size: 0.75rem;
          color: var(--text-tertiary);
        }

        .add-note-btn {
          display: inline-flex;
          align-items: center;
          gap: 0.375rem;
          padding: 0.5rem 0.75rem;
          background: transparent;
          border: 1px dashed var(--border);
          border-radius: 0.375rem;
          color: var(--text-secondary);
          font-size: 0.75rem;
          cursor: pointer;
          transition: all 0.15s ease;
        }

        .add-note-btn:hover {
          border-color: var(--primary);
          color: var(--primary);
        }

        .empty-selection {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          text-align: center;
          padding: 3rem;
        }

        .empty-selection .empty-icon {
          color: var(--text-tertiary);
          margin-bottom: 1rem;
        }

        .empty-selection h3 {
          margin: 0 0 0.5rem 0;
        }

        .empty-selection p {
          color: var(--text-secondary);
          margin: 0;
        }

        .empty-state {
          color: var(--text-secondary);
          text-align: center;
          padding: 2rem;
        }

        .loading-state {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 1rem;
          padding: 2rem;
          color: var(--text-secondary);
        }

        .page-loading {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          min-height: 400px;
          gap: 1rem;
          color: var(--text-secondary);
        }

        @media (max-width: 768px) {
          .video-layout {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
    </div>
  );
}
