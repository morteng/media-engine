import { useState } from 'react';
import { Routes, Route } from 'react-router-dom';
import {
  useBrandVoice,
  useVoiceCheck,
  useBrandAssets,
  useBrandFiles,
  useBrandFile,
  useBrandNotes,
  useAddBrandNote,
  useUpdateBrandNote,
  useDeleteBrandNote,
} from '@/hooks/useApi';
import { Card, CardHeader, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { ProgressBar } from '@/components/ui/ProgressBar';
import { LoadingState } from '@/components/ui/Spinner';
import { SubTabs } from '@/components/ui/SubTabs';
import { Button } from '@/components/ui/Button';
import {
  MessageCircle,
  CheckCircle,
  AlertCircle,
  BookOpen,
  Users,
  FileText,
  Type,
  XCircle,
  Palette,
  Image,
  Folder,
  StickyNote,
  Plus,
  Trash2,
  Eye,
  Download,
} from 'lucide-react';
import './Brand.css';

const tabs = [
  { path: '', label: 'Overview' },
  { path: 'identity', label: 'Visual Identity' },
  { path: 'voice', label: 'Voice Profile' },
  { path: 'check', label: 'Voice Check' },
  { path: 'files', label: 'Files' },
  { path: 'notes', label: 'Notes' },
];

// ==================== OVERVIEW ====================

function OverviewView() {
  const { data: assets, isLoading: loadingAssets } = useBrandAssets();
  const { data: voice, isLoading: loadingVoice } = useBrandVoice();
  useBrandFiles();  // Prefetch for later use
  const { data: notes } = useBrandNotes();

  if (loadingAssets || loadingVoice) {
    return <LoadingState message="Loading brand overview..." />;
  }

  const logoCount = assets?.logos ? Object.keys(assets.logos).length : 0;
  const hasVoice = voice?.has_voice;
  const pendingNotes = notes?.notes.filter(n => n.status === 'pending').length || 0;

  return (
    <div className="brand-overview">
      {/* Brand Identity Card */}
      <Card className="brand-identity-card">
        <CardContent>
          <div className="brand-header">
            {assets?.logos?.primary?.exists && (
              <div className="brand-logo-preview">
                <LogoPreview path={assets.logos.primary.path} alt={assets.name} />
              </div>
            )}
            <div className="brand-info">
              <h1 className="brand-name">{assets?.name || 'Brand'}</h1>
              {assets?.identity?.taglines?.primary && (
                <p className="brand-tagline">{assets.identity.taglines.primary}</p>
              )}
              {assets?.identity?.legal?.copyright && (
                <p className="brand-copyright text-muted">{assets.identity.legal.copyright}</p>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Quick Stats */}
      <div className="brand-stats-grid">
        <Card>
          <CardContent className="stat-card">
            <Palette size={24} className="stat-icon" style={{ color: assets?.colors.brand.primary }} />
            <div className="stat-content">
              <span className="stat-value">
                {assets?.colors.brand ? Object.keys(assets.colors.brand).length : 0}
              </span>
              <span className="stat-label">Brand Colors</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="stat-card">
            <Image size={24} className="stat-icon" />
            <div className="stat-content">
              <span className="stat-value">{logoCount}</span>
              <span className="stat-label">Logo Variants</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="stat-card">
            <MessageCircle size={24} className="stat-icon" />
            <div className="stat-content">
              <span className="stat-value">{hasVoice ? 'Defined' : 'None'}</span>
              <span className="stat-label">Voice Profile</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="stat-card">
            <StickyNote size={24} className="stat-icon" />
            <div className="stat-content">
              <span className="stat-value">{pendingNotes}</span>
              <span className="stat-label">Pending Notes</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Color Palette Preview */}
      <Card>
        <CardHeader title="Color Palette" />
        <CardContent>
          <div className="color-palette-preview">
            <div className="color-group">
              <h4>Brand Colors</h4>
              <div className="color-swatches">
                {assets?.colors.brand && Object.entries(assets.colors.brand).map(([name, color]) => (
                  color && (
                    <div key={name} className="color-swatch-item">
                      <div
                        className="color-swatch"
                        style={{ backgroundColor: color as string }}
                        title={`${name}: ${color}`}
                      />
                      <span className="color-name">{name}</span>
                      <span className="color-value">{color as string}</span>
                    </div>
                  )
                ))}
              </div>
            </div>
            <div className="color-group">
              <h4>Semantic Colors</h4>
              <div className="color-swatches">
                {assets?.colors.semantic && Object.entries(assets.colors.semantic).map(([name, color]) => (
                  <div key={name} className="color-swatch-item">
                    <div
                      className="color-swatch"
                      style={{ backgroundColor: color }}
                      title={`${name}: ${color}`}
                    />
                    <span className="color-name">{name}</span>
                    <span className="color-value">{color}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Typography Preview */}
      <Card>
        <CardHeader title="Typography" />
        <CardContent>
          <div className="typography-preview">
            {assets?.typography?.fonts && Object.entries(assets.typography.fonts).map(([role, font]) => (
              <div key={role} className="font-preview">
                <div className="font-role">{role}</div>
                <div
                  className="font-sample"
                  style={{ fontFamily: `${font.family}, ${font.fallback || 'sans-serif'}` }}
                >
                  {font.family}
                </div>
                <div className="font-meta">
                  <Badge variant="default">{font.source}</Badge>
                  <span className="font-weights">Weights: {font.weights.join(', ')}</span>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Voice Summary */}
      {hasVoice && (
        <Card>
          <CardHeader title="Voice Profile Summary" />
          <CardContent>
            <div className="voice-summary">
              <div className="voice-personality">
                {voice.personality?.map((trait: string) => (
                  <Badge key={trait} variant="accent">{trait}</Badge>
                ))}
              </div>
              <div className="voice-details">
                <span>Tone: <strong>{voice.tone}</strong></span>
                <span>Formality: <strong>Level {voice.formality_level}</strong></span>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// ==================== VISUAL IDENTITY ====================

function VisualIdentityView() {
  const { data: assets, isLoading } = useBrandAssets();
  const [selectedLogo, setSelectedLogo] = useState<string | null>(null);

  if (isLoading) {
    return <LoadingState message="Loading visual identity..." />;
  }

  return (
    <div className="visual-identity">
      {/* Logos Section */}
      <Card>
        <CardHeader title="Logos" />
        <CardContent>
          <div className="logos-grid">
            {assets?.logos && Object.entries(assets.logos).map(([variant, logo]) => (
              <div
                key={variant}
                className={`logo-card ${selectedLogo === variant ? 'selected' : ''} ${!logo.exists ? 'missing' : ''}`}
                onClick={() => setSelectedLogo(variant)}
              >
                <div className="logo-preview-container">
                  {logo.exists ? (
                    <LogoPreview path={logo.path} alt={logo.alt} />
                  ) : (
                    <div className="logo-placeholder">
                      <Image size={32} className="text-muted" />
                      <span>Not found</span>
                    </div>
                  )}
                </div>
                <div className="logo-info">
                  <span className="logo-variant">{variant}</span>
                  <span className="logo-path text-muted">{logo.path}</span>
                </div>
                {logo.exists && (
                  <div className="logo-actions">
                    <Button size="sm" variant="ghost" title="Preview">
                      <Eye size={14} />
                    </Button>
                    <Button size="sm" variant="ghost" title="Download">
                      <Download size={14} />
                    </Button>
                  </div>
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Colors Section */}
      <Card>
        <CardHeader title="Color System" />
        <CardContent>
          <div className="color-system">
            {/* Brand Colors */}
            <div className="color-section">
              <h4>Brand Colors</h4>
              <div className="color-grid">
                {assets?.colors.brand && Object.entries(assets.colors.brand).map(([name, color]) => (
                  color && (
                    <div key={name} className="color-card">
                      <div className="color-preview" style={{ backgroundColor: color as string }} />
                      <div className="color-details">
                        <span className="color-name">{name}</span>
                        <code className="color-hex">{color as string}</code>
                      </div>
                    </div>
                  )
                ))}
              </div>
            </div>

            {/* Semantic Colors */}
            <div className="color-section">
              <h4>Semantic Colors</h4>
              <div className="color-grid">
                {assets?.colors.semantic && Object.entries(assets.colors.semantic).map(([name, color]) => (
                  <div key={name} className="color-card">
                    <div className="color-preview" style={{ backgroundColor: color }} />
                    <div className="color-details">
                      <span className="color-name">{name}</span>
                      <code className="color-hex">{color}</code>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Text Colors */}
            {assets?.colors.text && (
              <div className="color-section">
                <h4>Text Colors</h4>
                <div className="color-grid">
                  {Object.entries(assets.colors.text).map(([name, color]) => (
                    <div key={name} className="color-card">
                      <div className="color-preview" style={{ backgroundColor: color }} />
                      <div className="color-details">
                        <span className="color-name">{name}</span>
                        <code className="color-hex">{color}</code>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Typography Section */}
      <Card>
        <CardHeader title="Typography System" />
        <CardContent>
          <div className="typography-system">
            {assets?.typography?.fonts && Object.entries(assets.typography.fonts).map(([role, font]) => (
              <div key={role} className="typography-card">
                <div className="typography-header">
                  <Type size={20} />
                  <h4>{role.charAt(0).toUpperCase() + role.slice(1)}</h4>
                </div>
                <div
                  className="typography-sample"
                  style={{ fontFamily: `${font.family}, ${font.fallback || 'sans-serif'}` }}
                >
                  <span className="sample-large">Aa Bb Cc</span>
                  <span className="sample-text">The quick brown fox jumps over the lazy dog</span>
                </div>
                <div className="typography-meta">
                  <div className="meta-row">
                    <span className="meta-label">Family:</span>
                    <span className="meta-value">{font.family}</span>
                  </div>
                  <div className="meta-row">
                    <span className="meta-label">Weights:</span>
                    <span className="meta-value">{font.weights.join(', ')}</span>
                  </div>
                  <div className="meta-row">
                    <span className="meta-label">Source:</span>
                    <Badge variant="default">{font.source}</Badge>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// ==================== VOICE PROFILE ====================

function VoiceProfileView() {
  const { data: voice, isLoading } = useBrandVoice();

  if (isLoading) {
    return <LoadingState message="Loading voice profile..." />;
  }

  if (!voice?.has_voice) {
    return (
      <Card>
        <CardContent className="empty-state">
          <MessageCircle size={48} className="text-muted" />
          <h3>No Voice Profile</h3>
          <p className="text-muted">
            {voice?.warning || 'Add a voice section to your brand.yaml to define voice guidelines.'}
          </p>
        </CardContent>
      </Card>
    );
  }

  const formalityLabels: Record<number, string> = {
    1: 'Very Casual',
    2: 'Casual',
    3: 'Professional',
    4: 'Formal',
    5: 'Very Formal',
  };

  return (
    <div className="voice-profile-view">
      {/* Personality & Tone */}
      <Card>
        <CardHeader title="Personality & Tone" />
        <CardContent>
          <div className="personality-section">
            <h4>Personality Traits</h4>
            <div className="personality-tags">
              {voice.personality?.map((trait: string) => (
                <Badge key={trait} variant="accent">{trait}</Badge>
              ))}
            </div>
          </div>

          <div className="tone-section">
            <div className="tone-item">
              <span className="tone-label">Tone:</span>
              <Badge variant="default">{voice.tone}</Badge>
            </div>
            <div className="tone-item">
              <span className="tone-label">Formality:</span>
              <div className="formality-scale">
                {[1, 2, 3, 4, 5].map(level => (
                  <div
                    key={level}
                    className={`formality-level ${level === voice.formality_level ? 'active' : ''}`}
                    title={formalityLabels[level]}
                  >
                    {level}
                  </div>
                ))}
              </div>
              <span className="formality-label">{formalityLabels[voice.formality_level]}</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Style Guidelines */}
      <Card>
        <CardHeader title="Style Guidelines" />
        <CardContent>
          <div className="style-guidelines">
            <div className="style-item">
              <span className="style-label">Active Voice Target</span>
              <ProgressBar
                value={voice.style.active_voice_target * 100}
                max={100}
                showLabel
              />
            </div>
            <div className="style-item">
              <span className="style-label">Sentence Length</span>
              <span className="style-value">{voice.style.sentence_length_target} words avg</span>
            </div>
            <div className="style-item">
              <span className="style-label">Paragraph Max</span>
              <span className="style-value">{voice.style.paragraph_length_max} sentences</span>
            </div>
            <div className="style-item">
              <span className="style-label">Contractions</span>
              <Badge variant={voice.style.use_contractions ? 'success' : 'default'}>
                {voice.style.use_contractions ? 'Allowed' : 'Avoid'}
              </Badge>
            </div>
            <div className="style-item">
              <span className="style-label">Person Usage</span>
              <div className="person-badges">
                {voice.style.use_first_person && <Badge variant="info">First Person</Badge>}
                {voice.style.use_second_person && <Badge variant="info">Second Person</Badge>}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Overrides */}
      {((voice.available_doc_types?.length ?? 0) > 0 || (voice.available_audiences?.length ?? 0) > 0) && (
        <Card>
          <CardHeader title="Context Overrides" />
          <CardContent>
            <div className="overrides-section">
              {(voice.available_doc_types?.length ?? 0) > 0 && (
                <div className="override-group">
                  <h4><FileText size={16} /> Document Types</h4>
                  <div className="override-items">
                    {voice.available_doc_types?.map((type: string) => (
                      <Badge key={type} variant="default">{type}</Badge>
                    ))}
                  </div>
                </div>
              )}
              {(voice.available_audiences?.length ?? 0) > 0 && (
                <div className="override-group">
                  <h4><Users size={16} /> Audiences</h4>
                  <div className="override-items">
                    {voice.available_audiences?.map((audience: string) => (
                      <Badge key={audience} variant="default">{audience}</Badge>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Terminology */}
      {((voice.preferred_terms?.length ?? 0) > 0 || (voice.avoid_phrases?.length ?? 0) > 0) && (
        <Card>
          <CardHeader title="Terminology Guidelines" />
          <CardContent>
            {(voice.preferred_terms?.length ?? 0) > 0 && (
              <div className="terminology-section">
                <h4>Preferred Terms</h4>
                <div className="terms-list">
                  {voice.preferred_terms?.slice(0, 5).map((term: { prefer: string; avoid: string[] }, i: number) => (
                    <div key={i} className="term-item">
                      <Badge variant="success">{term.prefer}</Badge>
                      <span className="term-arrow">instead of</span>
                      <span className="avoid-terms">{term.avoid.join(', ')}</span>
                    </div>
                  ))}
                  {(voice.preferred_terms?.length ?? 0) > 5 && (
                    <span className="more-terms">+{(voice.preferred_terms?.length ?? 0) - 5} more</span>
                  )}
                </div>
              </div>
            )}
            {(voice.avoid_phrases?.length ?? 0) > 0 && (
              <div className="terminology-section">
                <h4>Phrases to Avoid</h4>
                <div className="avoid-phrases">
                  {voice.avoid_phrases?.slice(0, 8).map((phrase: string) => (
                    <Badge key={phrase} variant="warning">{phrase}</Badge>
                  ))}
                  {(voice.avoid_phrases?.length ?? 0) > 8 && (
                    <span className="more-terms">+{(voice.avoid_phrases?.length ?? 0) - 8} more</span>
                  )}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// ==================== VOICE CHECK ====================

function VoiceCheckView() {
  const { data, isLoading } = useVoiceCheck();

  if (isLoading) {
    return <LoadingState message="Checking documents against voice guidelines..." />;
  }

  if (!data) {
    return (
      <Card>
        <CardContent className="empty-state">
          <AlertCircle size={48} className="text-muted" />
          <h3>No Voice Check Data</h3>
          <p className="text-muted">Unable to load voice check results.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="voice-check-view">
      {/* Summary */}
      <Card>
        <CardHeader title="Voice Compliance Summary" />
        <CardContent>
          <div className="compliance-summary">
            <div className="compliance-stat">
              <span className="stat-value">{data.summary.pass_rate}%</span>
              <span className="stat-label">Pass Rate</span>
            </div>
            <div className="compliance-stat">
              <span className="stat-value">{data.summary.documents_passed}/{data.summary.documents_checked}</span>
              <span className="stat-label">Documents Passing</span>
            </div>
            <div className="compliance-stat">
              <span className="stat-value">{data.summary.total_issues}</span>
              <span className="stat-label">Total Issues</span>
            </div>
          </div>
          <ProgressBar
            value={data.summary.pass_rate}
            max={100}
            variant={data.summary.pass_rate >= 80 ? 'success' : data.summary.pass_rate >= 50 ? 'warning' : 'error'}
          />
        </CardContent>
      </Card>

      {/* Document Results */}
      <Card>
        <CardHeader title="Document Results" />
        <CardContent>
          <div className="document-results">
            {data.results.map((result) => (
              <div key={result.document} className={`result-item ${result.passed ? 'passed' : 'failed'}`}>
                <div className="result-header">
                  {result.passed ? (
                    <CheckCircle size={18} className="result-icon success" />
                  ) : (
                    <XCircle size={18} className="result-icon error" />
                  )}
                  <span className="result-name">{result.document_name}</span>
                  <Badge variant={result.passed ? 'success' : 'warning'}>
                    {result.issues.length} issues
                  </Badge>
                </div>
                {result.issues.length > 0 && (
                  <div className="result-issues">
                    {result.issues.map((issue, i) => (
                      <div key={i} className="issue-item">
                        <Badge
                          variant={issue.severity === 'error' ? 'error' : issue.severity === 'warning' ? 'warning' : 'info'}
                          size="sm"
                        >
                          {issue.type}
                        </Badge>
                        <span className="issue-message">{issue.message}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// ==================== FILES ====================

function FilesView() {
  const { data, isLoading } = useBrandFiles();
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const { data: fileContent } = useBrandFile(selectedFile || '');

  if (isLoading) {
    return <LoadingState message="Loading brand files..." />;
  }

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'logo': return <Image size={16} />;
      case 'configuration': return <FileText size={16} />;
      case 'template': return <BookOpen size={16} />;
      case 'font': return <Type size={16} />;
      default: return <Folder size={16} />;
    }
  };

  return (
    <div className="files-view">
      {/* File Categories */}
      <Card>
        <CardHeader title="Brand Files" />
        <CardContent>
          <div className="file-categories">
            {data?.categories && Object.entries(data.categories).map(([category, count]) => (
              count > 0 && (
                <div key={category} className="category-badge">
                  {getCategoryIcon(category)}
                  <span>{category}</span>
                  <Badge variant="default" size="sm">{count}</Badge>
                </div>
              )
            ))}
          </div>
        </CardContent>
      </Card>

      {/* File List */}
      <div className="files-grid">
        <Card className="file-list-card">
          <CardHeader title={`Files (${data?.total || 0})`} />
          <CardContent>
            <div className="file-list">
              {data?.files.map((file) => (
                <div
                  key={file.path}
                  className={`file-item ${selectedFile === file.path ? 'selected' : ''}`}
                  onClick={() => setSelectedFile(file.path)}
                >
                  {getCategoryIcon(file.category)}
                  <div className="file-info">
                    <span className="file-name">{file.path.split('/').pop()}</span>
                    <span className="file-path text-muted">{file.path}</span>
                  </div>
                  <div className="file-meta">
                    <Badge variant="default" size="sm">{file.type}</Badge>
                    {file.legacy && <Badge variant="warning" size="sm">legacy</Badge>}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* File Preview */}
        <Card className="file-preview-card">
          <CardHeader title="Preview" />
          <CardContent>
            {selectedFile && fileContent ? (
              <div className="file-preview">
                {fileContent.encoding === 'base64' && fileContent.mime_type.startsWith('image/') ? (
                  <img
                    src={`data:${fileContent.mime_type};base64,${fileContent.content}`}
                    alt={fileContent.name}
                    className="preview-image"
                  />
                ) : fileContent.encoding === 'text' ? (
                  <pre className="preview-text">{fileContent.content}</pre>
                ) : (
                  <div className="preview-binary">
                    <FileText size={48} className="text-muted" />
                    <p>Binary file - {fileContent.size} bytes</p>
                  </div>
                )}
              </div>
            ) : (
              <div className="preview-empty">
                <Eye size={48} className="text-muted" />
                <p>Select a file to preview</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

// ==================== NOTES ====================

function NotesView() {
  const { data, isLoading } = useBrandNotes();
  const addNote = useAddBrandNote();
  const updateNote = useUpdateBrandNote();
  const deleteNote = useDeleteBrandNote();

  const [showAddForm, setShowAddForm] = useState(false);
  const [newNote, setNewNote] = useState({ category: 'general', text: '', priority: 'medium' });

  if (isLoading) {
    return <LoadingState message="Loading brand notes..." />;
  }

  const handleAddNote = async () => {
    if (!newNote.text.trim()) return;
    await addNote.mutateAsync(newNote);
    setNewNote({ category: 'general', text: '', priority: 'medium' });
    setShowAddForm(false);
  };

  const handleStatusChange = async (noteId: string, status: string) => {
    await updateNote.mutateAsync({ noteId, status });
  };

  const handleDelete = async (noteId: string) => {
    if (confirm('Delete this note?')) {
      await deleteNote.mutateAsync(noteId);
    }
  };

  const pendingNotes = data?.notes.filter(n => n.status === 'pending') || [];
  const completedNotes = data?.notes.filter(n => n.status === 'completed') || [];

  const priorityColors: Record<string, 'default' | 'info' | 'warning' | 'error'> = {
    low: 'default',
    medium: 'info',
    high: 'warning',
    critical: 'error',
  };

  return (
    <div className="notes-view">
      {/* Add Note */}
      <Card>
        <CardHeader
          title="Brand Notes for AI Processing"
          action={
            <Button size="sm" onClick={() => setShowAddForm(!showAddForm)}>
              <Plus size={14} /> Add Note
            </Button>
          }
        />
        <CardContent>
          <p className="notes-description text-muted">
            Add notes about brand elements for AI to process. Notes can target specific files or general guidelines.
          </p>

          {showAddForm && (
            <div className="add-note-form">
              <div className="form-row">
                <select
                  value={newNote.category}
                  onChange={(e) => setNewNote({ ...newNote, category: e.target.value })}
                  className="form-select"
                >
                  {data?.categories.map(cat => (
                    <option key={cat} value={cat}>{cat}</option>
                  ))}
                </select>
                <select
                  value={newNote.priority}
                  onChange={(e) => setNewNote({ ...newNote, priority: e.target.value })}
                  className="form-select"
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="critical">Critical</option>
                </select>
              </div>
              <textarea
                value={newNote.text}
                onChange={(e) => setNewNote({ ...newNote, text: e.target.value })}
                placeholder="Enter your note for AI processing..."
                className="form-textarea"
                rows={3}
              />
              <div className="form-actions">
                <Button variant="ghost" onClick={() => setShowAddForm(false)}>Cancel</Button>
                <Button onClick={handleAddNote} disabled={!newNote.text.trim()}>
                  Add Note
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Pending Notes */}
      <Card>
        <CardHeader title={`Pending Notes (${pendingNotes.length})`} />
        <CardContent>
          {pendingNotes.length === 0 ? (
            <p className="text-muted">No pending notes</p>
          ) : (
            <div className="notes-list">
              {pendingNotes.map((note) => (
                <div key={note.id} className="note-item">
                  <div className="note-header">
                    <Badge variant={priorityColors[note.priority]}>
                      {note.priority}
                    </Badge>
                    <Badge variant="default">{note.category}</Badge>
                    {note.target && <span className="note-target">{note.target}</span>}
                  </div>
                  <p className="note-text">{note.text}</p>
                  <div className="note-actions">
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => handleStatusChange(note.id, 'completed')}
                    >
                      <CheckCircle size={14} /> Complete
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => handleDelete(note.id)}
                    >
                      <Trash2 size={14} />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Completed Notes */}
      {completedNotes.length > 0 && (
        <Card>
          <CardHeader title={`Completed (${completedNotes.length})`} />
          <CardContent>
            <div className="notes-list completed">
              {completedNotes.slice(0, 5).map((note) => (
                <div key={note.id} className="note-item completed">
                  <div className="note-header">
                    <Badge variant="success">completed</Badge>
                    <Badge variant="default">{note.category}</Badge>
                  </div>
                  <p className="note-text">{note.text}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// ==================== HELPER COMPONENTS ====================

function LogoPreview({ path, alt }: { path: string; alt: string }) {
  const { data, isLoading } = useBrandFile(path);

  if (isLoading || !data) {
    return <div className="logo-loading" />;
  }

  if (data.encoding === 'base64' && data.mime_type.startsWith('image/')) {
    return (
      <img
        src={`data:${data.mime_type};base64,${data.content}`}
        alt={alt}
        className="logo-image"
      />
    );
  }

  return <div className="logo-placeholder"><Image size={24} /></div>;
}

// ==================== MAIN COMPONENT ====================

export function Brand() {
  return (
    <div className="brand-page">
      <div className="page-header">
        <h1>Brand Hub</h1>
        <p className="text-muted">Visual identity, voice guidelines, and brand assets</p>
      </div>

      <SubTabs tabs={tabs} basePath="/brand" />

      <div className="brand-content">
        <Routes>
          <Route index element={<OverviewView />} />
          <Route path="identity" element={<VisualIdentityView />} />
          <Route path="voice" element={<VoiceProfileView />} />
          <Route path="check" element={<VoiceCheckView />} />
          <Route path="files" element={<FilesView />} />
          <Route path="notes" element={<NotesView />} />
        </Routes>
      </div>
    </div>
  );
}
