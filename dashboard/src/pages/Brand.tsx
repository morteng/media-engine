import { useState, useCallback } from 'react';
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
import { SubTabs, ExpandableSection, Spinner } from '@/components/ui';
import { InfoTooltip } from '@/components/ui/InfoTooltip';
import {
  MessageCircle,
  CheckCircle,
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
  Copy,
  Sparkles,
  Shield,
} from 'lucide-react';

// Consolidated to 2 tabs
const tabs = [
  { path: '', label: 'Design System' },
  { path: 'voice', label: 'Voice & Guidelines' },
];

// Helper hook for copy to clipboard
function useCopyToClipboard() {
  const [copiedValue, setCopiedValue] = useState<string | null>(null);

  const copy = useCallback((text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedValue(text);
    setTimeout(() => setCopiedValue(null), 2000);
  }, []);

  return { copy, copiedValue };
}

// Loading component
function Loading({ message }: { message: string }) {
  return (
    <div className="flex items-center justify-center min-h-[400px]">
      <div className="text-center">
        <Spinner size="lg" className="text-primary" />
        <p className="mt-4 text-base-content/60">{message}</p>
      </div>
    </div>
  );
}

// ==================== DESIGN SYSTEM TAB ====================

function DesignSystemView() {
  const { data: assets, isLoading: loadingAssets } = useBrandAssets();
  const { data: voice, isLoading: loadingVoice } = useBrandVoice();
  const { data: files } = useBrandFiles();
  const { copy, copiedValue } = useCopyToClipboard();
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const { data: fileContent } = useBrandFile(selectedFile || '');

  if (loadingAssets || loadingVoice) {
    return <Loading message="Loading design system..." />;
  }

  const logoCount = assets?.logos ? Object.keys(assets.logos).length : 0;
  const hasVoice = voice?.has_voice;
  const colorCount = assets?.colors.brand ? Object.keys(assets.colors.brand).length : 0;
  const fontCount = assets?.typography?.fonts ? Object.keys(assets.typography.fonts).length : 0;

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
    <div className="space-y-6">
      {/* Brand Hero Card */}
      <div className="card bg-gradient-to-br from-base-200 to-base-300 border border-primary/20">
        <div className="card-body">
          <div className="flex flex-col md:flex-row items-center gap-6">
            <div className="w-24 h-24 rounded-xl bg-base-100 flex items-center justify-center overflow-hidden">
              {assets?.logos?.primary?.exists ? (
                <LogoPreview path={assets.logos.primary.path} alt={assets.name} />
              ) : (
                <Sparkles size={48} className="text-primary" />
              )}
            </div>
            <div className="flex-1 text-center md:text-left">
              <h2 className="text-2xl font-bold">{assets?.name || 'Your Brand'}</h2>
              {assets?.identity?.taglines?.primary && (
                <p className="text-base-content/70 mt-1">{assets.identity.taglines.primary}</p>
              )}
              <div className="flex flex-wrap gap-2 mt-3 justify-center md:justify-start">
                <div className="badge badge-primary">{colorCount} Colors</div>
                <div className="badge badge-info">{logoCount} Logos</div>
                <div className="badge badge-success">{fontCount} Fonts</div>
                {hasVoice && <div className="badge badge-ghost">Voice Defined</div>}
              </div>
              {assets?.identity?.legal?.copyright && (
                <p className="text-xs text-base-content/50 mt-3">{assets.identity.legal.copyright}</p>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="card bg-base-200">
          <div className="card-body p-4 flex flex-row items-center gap-3">
            <div className="w-10 h-10 rounded-lg flex items-center justify-center" style={{ background: `${assets?.colors.brand.primary}20` }}>
              <Palette size={20} style={{ color: assets?.colors.brand.primary }} />
            </div>
            <div>
              <div className="text-2xl font-bold">{colorCount}</div>
              <div className="text-xs text-base-content/60 flex items-center gap-1">
                Brand Colors
                <InfoTooltip title="Brand Colors" content="Primary brand palette colors used across all materials. Click colors to copy hex values." />
              </div>
            </div>
          </div>
        </div>

        <div className="card bg-base-200">
          <div className="card-body p-4 flex flex-row items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-accent/20 flex items-center justify-center">
              <Image size={20} className="text-accent" />
            </div>
            <div>
              <div className="text-2xl font-bold">{logoCount}</div>
              <div className="text-xs text-base-content/60 flex items-center gap-1">
                Logo Variants
                <InfoTooltip title="Logo Variants" content="Different logo versions for various use cases (primary, dark mode, icon, etc)." />
              </div>
            </div>
          </div>
        </div>

        <div className="card bg-base-200">
          <div className="card-body p-4 flex flex-row items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-info/20 flex items-center justify-center">
              <Type size={20} className="text-info" />
            </div>
            <div>
              <div className="text-2xl font-bold">{fontCount}</div>
              <div className="text-xs text-base-content/60 flex items-center gap-1">
                Font Families
                <InfoTooltip title="Font Families" content="Typography system fonts for headings, body text, and code." />
              </div>
            </div>
          </div>
        </div>

        <div className="card bg-base-200">
          <div className="card-body p-4 flex flex-row items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-warning/20 flex items-center justify-center">
              <Folder size={20} className="text-warning" />
            </div>
            <div>
              <div className="text-2xl font-bold">{files?.total || 0}</div>
              <div className="text-xs text-base-content/60 flex items-center gap-1">
                Brand Files
                <InfoTooltip title="Brand Files" content="All brand asset files including logos, fonts, and configuration." />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Logos Section */}
      <ExpandableSection
        title="Logos"
        description="Logo variants for different use cases"
        icon={<Image size={20} />}
        tooltip={{ title: "Brand Logos", content: "Logo files configured in brand.yaml. Use primary for most cases, dark for dark backgrounds, icon for favicons." }}
        defaultExpanded={true}
      >
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {assets?.logos && Object.entries(assets.logos).map(([variant, logo]) => (
            <div
              key={variant}
              className={`p-4 rounded-lg border-2 transition-all ${
                logo.exists
                  ? 'border-base-300 hover:border-primary/50 bg-base-100'
                  : 'border-dashed border-base-300 bg-base-100/50'
              }`}
            >
              <div className="aspect-square flex items-center justify-center mb-3 bg-base-200 rounded-lg">
                {logo.exists ? (
                  <LogoPreview path={logo.path} alt={logo.alt} />
                ) : (
                  <div className="text-center text-base-content/40">
                    <Image size={32} className="mx-auto mb-1" />
                    <span className="text-xs">Not found</span>
                  </div>
                )}
              </div>
              <div className="font-medium text-sm capitalize">{variant}</div>
              <div className="text-xs text-base-content/50 truncate">{logo.path}</div>
              {logo.exists && (
                <div className="flex gap-1 mt-2">
                  <button className="btn btn-ghost btn-xs" title="Preview">
                    <Eye size={14} />
                  </button>
                  <button className="btn btn-ghost btn-xs" title="Download">
                    <Download size={14} />
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      </ExpandableSection>

      {/* Color Palette */}
      <ExpandableSection
        title="Color Palette"
        description="Brand and semantic colors - click to copy"
        icon={<Palette size={20} />}
        tooltip={{ title: "Color System", content: "Brand colors define your visual identity. Semantic colors (success, warning, error) are used for UI feedback." }}
        defaultExpanded={true}
      >
        <div className="space-y-6">
          <div>
            <h4 className="text-sm font-medium mb-3">Brand Colors</h4>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {assets?.colors.brand && Object.entries(assets.colors.brand).map(([name, color]) => (
                color && (
                  <button
                    key={name}
                    className={`group relative p-3 rounded-lg border transition-all ${copiedValue === color ? 'border-success bg-success/10' : 'border-base-300 hover:border-primary/50 bg-base-100'}`}
                    onClick={() => copy(color as string)}
                  >
                    <div className="w-full h-12 rounded-md mb-2" style={{ backgroundColor: color as string }} />
                    <div className="text-left">
                      <div className="font-medium text-sm capitalize">{name}</div>
                      <code className="text-xs text-base-content/60">{color as string}</code>
                    </div>
                    <Copy size={14} className="absolute top-2 right-2 opacity-0 group-hover:opacity-50" />
                    {copiedValue === color && (
                      <span className="absolute top-2 right-2 text-xs text-success">Copied!</span>
                    )}
                  </button>
                )
              ))}
            </div>
          </div>

          <div>
            <h4 className="text-sm font-medium mb-3">Semantic Colors</h4>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {assets?.colors.semantic && Object.entries(assets.colors.semantic).map(([name, color]) => (
                <button
                  key={name}
                  className={`group relative p-3 rounded-lg border transition-all ${copiedValue === color ? 'border-success bg-success/10' : 'border-base-300 hover:border-primary/50 bg-base-100'}`}
                  onClick={() => copy(color)}
                >
                  <div className="w-full h-12 rounded-md mb-2" style={{ backgroundColor: color }} />
                  <div className="text-left">
                    <div className="font-medium text-sm capitalize">{name}</div>
                    <code className="text-xs text-base-content/60">{color}</code>
                  </div>
                  <Copy size={14} className="absolute top-2 right-2 opacity-0 group-hover:opacity-50" />
                  {copiedValue === color && (
                    <span className="absolute top-2 right-2 text-xs text-success">Copied!</span>
                  )}
                </button>
              ))}
            </div>
          </div>

          {/* Text Colors */}
          {assets?.colors.text && (
            <div>
              <h4 className="text-sm font-medium mb-3">Text Colors</h4>
              <div className="grid grid-cols-3 md:grid-cols-6 gap-3">
                {Object.entries(assets.colors.text).map(([name, color]) => (
                  <button
                    key={name}
                    className={`group relative p-2 rounded-lg border transition-all ${copiedValue === color ? 'border-success bg-success/10' : 'border-base-300 hover:border-primary/50 bg-base-100'}`}
                    onClick={() => copy(color)}
                  >
                    <div className="w-full h-8 rounded-md mb-1" style={{ backgroundColor: color }} />
                    <div className="text-xs text-center capitalize">{name}</div>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </ExpandableSection>

      {/* Typography */}
      <ExpandableSection
        title="Typography"
        description="Font families, weights, and scale"
        icon={<Type size={20} />}
        tooltip={{ title: "Typography System", content: "Fonts for different purposes: headings for titles, body for content, code for technical text." }}
      >
        <div className="space-y-4">
          {assets?.typography?.fonts && Object.entries(assets.typography.fonts).map(([role, font]) => (
            <div key={role} className="p-4 rounded-lg bg-base-100 border border-base-300">
              <div className="flex items-center gap-2 mb-4">
                <Type size={20} className="text-primary" />
                <h4 className="font-semibold capitalize">{role}</h4>
                <div className="badge badge-ghost badge-sm">{font.source}</div>
              </div>
              <div style={{ fontFamily: `${font.family}, ${font.fallback || 'sans-serif'}` }} className="mb-4">
                <div className="text-4xl font-semibold mb-2">Aa Bb Cc</div>
                <div className="text-base-content/70">The quick brown fox jumps over the lazy dog</div>
              </div>
              <div className="grid grid-cols-3 gap-4 text-sm">
                <div>
                  <span className="text-base-content/60">Family:</span>
                  <div className="font-medium">{font.family}</div>
                </div>
                <div>
                  <span className="text-base-content/60">Weights:</span>
                  <div className="font-medium">{font.weights.join(', ')}</div>
                </div>
                <div>
                  <span className="text-base-content/60">Fallback:</span>
                  <div className="font-medium">{font.fallback || 'sans-serif'}</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </ExpandableSection>

      {/* Brand Files */}
      <ExpandableSection
        title="Brand Files"
        description={`${files?.total || 0} files across ${Object.keys(files?.categories || {}).length} categories`}
        icon={<Folder size={20} />}
        tooltip={{ title: "Brand Assets", content: "All brand-related files including logos, configuration, and templates." }}
      >
        <div className="grid md:grid-cols-2 gap-6">
          <div>
            <h4 className="text-sm font-medium mb-3">Files</h4>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {files?.files.map((file) => (
                <div
                  key={file.path}
                  className={`p-3 rounded-lg cursor-pointer transition-all ${
                    selectedFile === file.path
                      ? 'bg-primary/10 border border-primary/30'
                      : 'bg-base-100 border border-base-300 hover:border-primary/30'
                  }`}
                  onClick={() => setSelectedFile(file.path)}
                >
                  <div className="flex items-center gap-3">
                    {getCategoryIcon(file.category)}
                    <div className="flex-1 min-w-0">
                      <div className="font-medium text-sm truncate">{file.path.split('/').pop()}</div>
                      <div className="text-xs text-base-content/50 truncate">{file.path}</div>
                    </div>
                    <div className="badge badge-ghost badge-xs">{file.type}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div>
            <h4 className="text-sm font-medium mb-3">Preview</h4>
            <div className="p-4 rounded-lg bg-base-100 border border-base-300 min-h-40">
              {selectedFile && fileContent ? (
                <div>
                  {fileContent.encoding === 'base64' && fileContent.mime_type.startsWith('image/') ? (
                    <img
                      src={`data:${fileContent.mime_type};base64,${fileContent.content}`}
                      alt={fileContent.name}
                      className="max-w-full rounded-lg"
                    />
                  ) : fileContent.encoding === 'text' ? (
                    <pre className="text-xs overflow-auto max-h-48">{fileContent.content}</pre>
                  ) : (
                    <div className="text-center py-8">
                      <FileText size={32} className="text-base-content/30 mx-auto mb-2" />
                      <p className="text-sm text-base-content/60">Binary file - {fileContent.size} bytes</p>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-center py-8">
                  <Eye size={32} className="text-base-content/30 mx-auto mb-2" />
                  <p className="text-sm text-base-content/60">Select a file to preview</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </ExpandableSection>
    </div>
  );
}

// ==================== VOICE & GUIDELINES TAB ====================

function VoiceView() {
  const { data: voice, isLoading: loadingVoice } = useBrandVoice();
  const { data: checkData, isLoading: loadingCheck } = useVoiceCheck();
  const { data: notes } = useBrandNotes();
  const addNote = useAddBrandNote();
  const updateNote = useUpdateBrandNote();
  const deleteNote = useDeleteBrandNote();

  const [showAddForm, setShowAddForm] = useState(false);
  const [newNote, setNewNote] = useState({ category: 'general', text: '', priority: 'medium' });

  if (loadingVoice || loadingCheck) {
    return <Loading message="Loading voice profile..." />;
  }

  const formalityLabels: Record<number, string> = {
    1: 'Very Casual',
    2: 'Casual',
    3: 'Professional',
    4: 'Formal',
    5: 'Very Formal',
  };

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

  const pendingNotes = notes?.notes.filter(n => n.status === 'pending') || [];
  const priorityColors: Record<string, string> = {
    low: 'badge-ghost',
    medium: 'badge-info',
    high: 'badge-warning',
    critical: 'badge-error',
  };

  if (!voice?.has_voice) {
    return (
      <div className="card bg-base-200">
        <div className="card-body items-center text-center py-16">
          <MessageCircle size={48} className="text-base-content/30 mb-4" />
          <h3 className="text-lg font-semibold">No Voice Profile</h3>
          <p className="text-base-content/60 max-w-md">
            {voice?.warning || 'Add a voice section to your brand.yaml to define voice guidelines.'}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Voice Summary Hero */}
      <div className="card bg-gradient-to-br from-base-200 to-base-300 border border-accent/20">
        <div className="card-body">
          <div className="flex flex-col md:flex-row items-center gap-6">
            <div className="w-20 h-20 rounded-xl bg-accent/20 flex items-center justify-center">
              <MessageCircle size={36} className="text-accent" />
            </div>
            <div className="flex-1 text-center md:text-left">
              <h2 className="text-xl font-bold flex items-center gap-2 justify-center md:justify-start">
                Voice Profile
                <InfoTooltip title="Brand Voice" content="Defines how your brand communicates - personality, tone, and style guidelines for consistent messaging." />
              </h2>
              <div className="flex flex-wrap gap-2 mt-3 justify-center md:justify-start">
                {voice.personality?.map((trait: string) => (
                  <div key={trait} className="badge badge-accent">{trait}</div>
                ))}
              </div>
              <div className="flex gap-6 mt-3 justify-center md:justify-start text-sm">
                <div>
                  <span className="text-base-content/60">Tone:</span>
                  <span className="ml-1 font-medium">{voice.tone}</span>
                </div>
                <div>
                  <span className="text-base-content/60">Formality:</span>
                  <span className="ml-1 font-medium">{formalityLabels[voice.formality_level]}</span>
                </div>
              </div>
            </div>
            {checkData && (
              <div className="text-center">
                <div className={`text-3xl font-bold ${checkData.summary.pass_rate >= 80 ? 'text-success' : checkData.summary.pass_rate >= 50 ? 'text-warning' : 'text-error'}`}>
                  {checkData.summary.pass_rate}%
                </div>
                <div className="text-xs text-base-content/60">Compliance</div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Voice Compliance Check */}
      {checkData && (
        <ExpandableSection
          title="Voice Compliance"
          description={`${checkData.summary.documents_passed}/${checkData.summary.documents_checked} documents passing`}
          icon={<Shield size={20} />}
          tooltip={{ title: "Voice Check", content: "Automated check of all documents against your voice guidelines. Shows compliance rate and specific issues." }}
          statusBadge={checkData.summary.total_issues > 0 ? 'warning' : 'success'}
          statusCount={checkData.summary.total_issues}
          defaultExpanded={checkData.summary.total_issues > 0}
        >
          <div className="space-y-4">
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center p-3 rounded-lg bg-base-100">
                <div className="text-2xl font-bold">{checkData.summary.pass_rate}%</div>
                <div className="text-xs text-base-content/60">Pass Rate</div>
              </div>
              <div className="text-center p-3 rounded-lg bg-base-100">
                <div className="text-2xl font-bold">{checkData.summary.documents_passed}/{checkData.summary.documents_checked}</div>
                <div className="text-xs text-base-content/60">Passing</div>
              </div>
              <div className="text-center p-3 rounded-lg bg-base-100">
                <div className="text-2xl font-bold">{checkData.summary.total_issues}</div>
                <div className="text-xs text-base-content/60">Issues</div>
              </div>
            </div>

            <progress
              className={`progress w-full ${
                checkData.summary.pass_rate >= 80 ? 'progress-success' :
                checkData.summary.pass_rate >= 50 ? 'progress-warning' : 'progress-error'
              }`}
              value={checkData.summary.pass_rate}
              max="100"
            ></progress>

            {/* Document Results */}
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {checkData.results.map((result) => (
                <div
                  key={result.document}
                  className={`p-3 rounded-lg border ${
                    result.passed ? 'bg-success/5 border-success/20' : 'bg-warning/5 border-warning/20'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    {result.passed ? (
                      <CheckCircle size={16} className="text-success flex-shrink-0" />
                    ) : (
                      <XCircle size={16} className="text-error flex-shrink-0" />
                    )}
                    <span className="font-medium flex-1 truncate">{result.document_name}</span>
                    <div className={`badge badge-sm ${result.passed ? 'badge-success' : 'badge-warning'}`}>
                      {result.issues.length}
                    </div>
                  </div>
                  {result.issues.length > 0 && (
                    <div className="mt-2 pl-7 space-y-1">
                      {result.issues.slice(0, 3).map((issue, i) => (
                        <div key={i} className="text-xs text-base-content/70">{issue.message}</div>
                      ))}
                      {result.issues.length > 3 && (
                        <div className="text-xs text-base-content/50">+{result.issues.length - 3} more</div>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </ExpandableSection>
      )}

      {/* Style Guidelines */}
      <ExpandableSection
        title="Style Guidelines"
        description="Writing style targets and preferences"
        icon={<BookOpen size={20} />}
        tooltip={{ title: "Style Guidelines", content: "Quantitative targets for writing style: active voice percentage, sentence length, and more." }}
      >
        <div className="grid md:grid-cols-2 gap-4">
          <div className="p-4 rounded-lg bg-base-100">
            <div className="text-sm text-base-content/60 mb-2 flex items-center gap-1">
              Active Voice Target
              <InfoTooltip title="Active Voice" content="Percentage of sentences that should use active voice (subject acts) rather than passive voice (subject receives action)." />
            </div>
            <progress className="progress progress-primary w-full" value={voice.style.active_voice_target * 100} max="100"></progress>
            <div className="text-right text-sm mt-1">{Math.round(voice.style.active_voice_target * 100)}%</div>
          </div>
          <div className="p-4 rounded-lg bg-base-100">
            <div className="text-sm text-base-content/60 mb-2">Sentence Length</div>
            <div className="text-2xl font-bold">{voice.style.sentence_length_target}</div>
            <div className="text-xs text-base-content/60">words average target</div>
          </div>
          <div className="p-4 rounded-lg bg-base-100">
            <div className="text-sm text-base-content/60 mb-2">Paragraph Max</div>
            <div className="text-2xl font-bold">{voice.style.paragraph_length_max}</div>
            <div className="text-xs text-base-content/60">sentences</div>
          </div>
          <div className="p-4 rounded-lg bg-base-100">
            <div className="text-sm text-base-content/60 mb-2">Writing Preferences</div>
            <div className="flex flex-wrap gap-2">
              <div className={`badge ${voice.style.use_contractions ? 'badge-success' : 'badge-ghost'}`}>
                {voice.style.use_contractions ? 'Contractions OK' : 'No Contractions'}
              </div>
              {voice.style.use_first_person && <div className="badge badge-info">First Person</div>}
              {voice.style.use_second_person && <div className="badge badge-info">Second Person</div>}
            </div>
          </div>
        </div>
      </ExpandableSection>

      {/* Terminology */}
      {((voice.preferred_terms?.length ?? 0) > 0 || (voice.avoid_phrases?.length ?? 0) > 0) && (
        <ExpandableSection
          title="Terminology"
          description="Preferred terms and phrases to avoid"
          icon={<FileText size={20} />}
          tooltip={{ title: "Terminology Guidelines", content: "Defines specific words to use and phrases to avoid for brand consistency." }}
        >
          <div className="space-y-4">
            {(voice.preferred_terms?.length ?? 0) > 0 && (
              <div>
                <h4 className="font-medium mb-3">Preferred Terms</h4>
                <div className="space-y-2">
                  {voice.preferred_terms?.slice(0, 8).map((term: { prefer: string; avoid: string[] }, i: number) => (
                    <div key={i} className="flex items-center gap-2 text-sm">
                      <div className="badge badge-success">{term.prefer}</div>
                      <span className="text-base-content/60">instead of</span>
                      <span className="text-base-content/80">{term.avoid.join(', ')}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
            {(voice.avoid_phrases?.length ?? 0) > 0 && (
              <div>
                <h4 className="font-medium mb-3">Phrases to Avoid</h4>
                <div className="flex flex-wrap gap-2">
                  {voice.avoid_phrases?.slice(0, 12).map((phrase: string) => (
                    <div key={phrase} className="badge badge-warning">{phrase}</div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </ExpandableSection>
      )}

      {/* Context Overrides */}
      {((voice.available_doc_types?.length ?? 0) > 0 || (voice.available_audiences?.length ?? 0) > 0) && (
        <ExpandableSection
          title="Context Overrides"
          description="Voice adjustments for document types and audiences"
          icon={<Users size={20} />}
          tooltip={{ title: "Context Overrides", content: "Voice profile adjustments for specific document types or target audiences." }}
        >
          <div className="grid md:grid-cols-2 gap-6">
            {(voice.available_doc_types?.length ?? 0) > 0 && (
              <div>
                <div className="flex items-center gap-2 mb-3">
                  <FileText size={16} className="text-primary" />
                  <h4 className="font-medium">Document Types</h4>
                </div>
                <div className="flex flex-wrap gap-2">
                  {voice.available_doc_types?.map((type: string) => (
                    <div key={type} className="badge badge-ghost">{type}</div>
                  ))}
                </div>
              </div>
            )}
            {(voice.available_audiences?.length ?? 0) > 0 && (
              <div>
                <div className="flex items-center gap-2 mb-3">
                  <Users size={16} className="text-primary" />
                  <h4 className="font-medium">Audiences</h4>
                </div>
                <div className="flex flex-wrap gap-2">
                  {voice.available_audiences?.map((audience: string) => (
                    <div key={audience} className="badge badge-ghost">{audience}</div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </ExpandableSection>
      )}

      {/* Brand Notes */}
      <ExpandableSection
        title="Brand Notes"
        description="Notes for AI processing and improvements"
        icon={<StickyNote size={20} />}
        tooltip={{ title: "Brand Notes", content: "Add notes for AI to process - suggestions for brand improvements, terminology updates, etc." }}
        statusBadge={pendingNotes.length > 0 ? 'info' : undefined}
        statusCount={pendingNotes.length}
      >
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <p className="text-sm text-base-content/60">
              Add notes for AI to process when updating brand guidelines.
            </p>
            <button className="btn btn-primary btn-sm" onClick={() => setShowAddForm(!showAddForm)}>
              <Plus size={14} /> Add Note
            </button>
          </div>

          {showAddForm && (
            <div className="p-4 rounded-lg bg-base-100 border border-base-300 space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <select
                  value={newNote.category}
                  onChange={(e) => setNewNote({ ...newNote, category: e.target.value })}
                  className="select select-bordered select-sm w-full"
                >
                  {notes?.categories.map(cat => (
                    <option key={cat} value={cat}>{cat}</option>
                  ))}
                </select>
                <select
                  value={newNote.priority}
                  onChange={(e) => setNewNote({ ...newNote, priority: e.target.value })}
                  className="select select-bordered select-sm w-full"
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
                placeholder="Enter your note..."
                className="textarea textarea-bordered w-full"
                rows={2}
              />
              <div className="flex justify-end gap-2">
                <button className="btn btn-ghost btn-sm" onClick={() => setShowAddForm(false)}>Cancel</button>
                <button className="btn btn-primary btn-sm" onClick={handleAddNote} disabled={!newNote.text.trim()}>
                  Add
                </button>
              </div>
            </div>
          )}

          {pendingNotes.length > 0 ? (
            <div className="space-y-2">
              {pendingNotes.map((note) => (
                <div key={note.id} className="p-3 rounded-lg bg-base-100 border border-base-300">
                  <div className="flex items-center gap-2 mb-2">
                    <div className={`badge badge-sm ${priorityColors[note.priority]}`}>{note.priority}</div>
                    <div className="badge badge-ghost badge-sm">{note.category}</div>
                  </div>
                  <p className="text-sm">{note.text}</p>
                  <div className="flex gap-2 mt-2">
                    <button
                      className="btn btn-ghost btn-xs"
                      onClick={() => handleStatusChange(note.id, 'completed')}
                    >
                      <CheckCircle size={12} /> Done
                    </button>
                    <button
                      className="btn btn-ghost btn-xs text-error"
                      onClick={() => handleDelete(note.id)}
                    >
                      <Trash2 size={12} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-base-content/50 text-center py-4">No pending notes</p>
          )}
        </div>
      </ExpandableSection>
    </div>
  );
}

// ==================== HELPER COMPONENTS ====================

function LogoPreview({ path, alt }: { path: string; alt: string }) {
  const { data, isLoading } = useBrandFile(path);

  if (isLoading || !data) {
    return <Spinner size="sm" />;
  }

  if (data.encoding === 'base64' && data.mime_type.startsWith('image/')) {
    return (
      <img
        src={`data:${data.mime_type};base64,${data.content}`}
        alt={alt}
        className="max-w-full max-h-full object-contain"
      />
    );
  }

  return <Image size={24} className="text-base-content/30" />;
}

// ==================== MAIN COMPONENT ====================

export function Brand() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-semibold">Brand</h1>
        <SubTabs tabs={tabs} basePath="/brand" />
      </div>

      <Routes>
        <Route index element={<DesignSystemView />} />
        <Route path="voice" element={<VoiceView />} />
      </Routes>
    </div>
  );
}
