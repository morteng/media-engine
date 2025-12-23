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
import { SubTabs } from '@/components/ui/SubTabs';
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
  Copy,
  Sparkles,
} from 'lucide-react';

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

const tabs = [
  { path: '', label: 'Overview' },
  { path: 'identity', label: 'Visual Identity' },
  { path: 'voice', label: 'Voice Profile' },
  { path: 'check', label: 'Voice Check' },
  { path: 'files', label: 'Files' },
  { path: 'notes', label: 'Notes' },
];

// ==================== LOADING STATE ====================

function LoadingSpinner({ message = 'Loading...' }: { message?: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-4 py-16">
      <span className="loading loading-spinner loading-lg text-primary"></span>
      <p className="text-base-content/60">{message}</p>
    </div>
  );
}

// ==================== OVERVIEW ====================

function OverviewView() {
  const { data: assets, isLoading: loadingAssets } = useBrandAssets();
  const { data: voice, isLoading: loadingVoice } = useBrandVoice();
  useBrandFiles();
  const { data: notes } = useBrandNotes();
  const { copy, copiedValue } = useCopyToClipboard();

  if (loadingAssets || loadingVoice) {
    return <LoadingSpinner message="Loading brand overview..." />;
  }

  const logoCount = assets?.logos ? Object.keys(assets.logos).length : 0;
  const hasVoice = voice?.has_voice;
  const pendingNotes = notes?.notes.filter(n => n.status === 'pending').length || 0;
  const colorCount = assets?.colors.brand ? Object.keys(assets.colors.brand).length : 0;
  const fontCount = assets?.typography?.fonts ? Object.keys(assets.typography.fonts).length : 0;

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
              <div className="text-xs text-base-content/60">Brand Colors</div>
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
              <div className="text-xs text-base-content/60">Logo Variants</div>
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
              <div className="text-xs text-base-content/60">Font Families</div>
            </div>
          </div>
        </div>

        <div className="card bg-base-200">
          <div className="card-body p-4 flex flex-row items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-warning/20 flex items-center justify-center">
              <StickyNote size={20} className="text-warning" />
            </div>
            <div>
              <div className="text-2xl font-bold">{pendingNotes}</div>
              <div className="text-xs text-base-content/60">Pending Notes</div>
            </div>
          </div>
        </div>
      </div>

      {/* Color Palette Preview */}
      <div className="card bg-base-200">
        <div className="card-body">
          <h3 className="card-title text-lg">Color Palette</h3>
          <p className="text-sm text-base-content/60 -mt-2">Click to copy hex value</p>

          <div className="space-y-6 mt-4">
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
          </div>
        </div>
      </div>

      {/* Typography Preview */}
      <div className="card bg-base-200">
        <div className="card-body">
          <h3 className="card-title text-lg">Typography</h3>
          <p className="text-sm text-base-content/60 -mt-2">Font families and weights</p>

          <div className="grid md:grid-cols-2 gap-4 mt-4">
            {assets?.typography?.fonts && Object.entries(assets.typography.fonts).map(([role, font]) => (
              <div key={role} className="p-4 rounded-lg bg-base-100 border border-base-300">
                <div className="flex items-center gap-2 mb-3">
                  <Type size={16} className="text-accent" />
                  <span className="font-medium capitalize">{role}</span>
                  <div className="badge badge-ghost badge-sm">{font.source}</div>
                </div>
                <div style={{ fontFamily: `${font.family}, ${font.fallback || 'sans-serif'}` }}>
                  <div className="text-2xl font-semibold mb-1">{font.family}</div>
                  <div className="text-xs text-base-content/50 truncate">
                    ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789
                  </div>
                </div>
                <div className="flex items-center gap-2 mt-3">
                  <span className="text-xs text-base-content/60">Weights:</span>
                  <div className="flex gap-1">
                    {font.weights.map((w: number) => (
                      <span key={w} className="badge badge-ghost badge-xs">{w}</span>
                    ))}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Voice Summary */}
      {hasVoice && (
        <div className="card bg-base-200">
          <div className="card-body">
            <h3 className="card-title text-lg">Voice Profile</h3>
            <p className="text-sm text-base-content/60 -mt-2">Brand personality and tone</p>

            <div className="flex flex-col md:flex-row gap-6 mt-4">
              <div className="flex items-start gap-3">
                <MessageCircle size={20} className="text-accent mt-1" />
                <div className="flex flex-wrap gap-2">
                  {voice.personality?.map((trait: string) => (
                    <div key={trait} className="badge badge-accent">{trait}</div>
                  ))}
                </div>
              </div>
              <div className="flex gap-6">
                <div>
                  <div className="text-xs text-base-content/60">Tone</div>
                  <div className="font-medium">{voice.tone}</div>
                </div>
                <div>
                  <div className="text-xs text-base-content/60">Formality</div>
                  <div className="font-medium">Level {voice.formality_level}/5</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ==================== VISUAL IDENTITY ====================

function VisualIdentityView() {
  const { data: assets, isLoading } = useBrandAssets();
  const [selectedLogo, setSelectedLogo] = useState<string | null>(null);

  if (isLoading) {
    return <LoadingSpinner message="Loading visual identity..." />;
  }

  return (
    <div className="space-y-6">
      {/* Logos Section */}
      <div className="card bg-base-200">
        <div className="card-body">
          <h3 className="card-title text-lg">Logos</h3>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
            {assets?.logos && Object.entries(assets.logos).map(([variant, logo]) => (
              <div
                key={variant}
                className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                  selectedLogo === variant
                    ? 'border-primary bg-primary/5'
                    : logo.exists
                      ? 'border-base-300 hover:border-primary/50 bg-base-100'
                      : 'border-dashed border-base-300 bg-base-100/50'
                }`}
                onClick={() => setSelectedLogo(variant)}
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
        </div>
      </div>

      {/* Colors Section */}
      <div className="card bg-base-200">
        <div className="card-body">
          <h3 className="card-title text-lg">Color System</h3>

          <div className="space-y-6 mt-4">
            {/* Brand Colors */}
            <div>
              <h4 className="text-sm font-medium mb-3">Brand Colors</h4>
              <div className="grid grid-cols-3 md:grid-cols-6 gap-3">
                {assets?.colors.brand && Object.entries(assets.colors.brand).map(([name, color]) => (
                  color && (
                    <div key={name} className="text-center">
                      <div className="w-full aspect-square rounded-lg mb-2 border border-base-300" style={{ backgroundColor: color as string }} />
                      <div className="text-sm font-medium capitalize">{name}</div>
                      <code className="text-xs text-base-content/60">{color as string}</code>
                    </div>
                  )
                ))}
              </div>
            </div>

            {/* Semantic Colors */}
            <div>
              <h4 className="text-sm font-medium mb-3">Semantic Colors</h4>
              <div className="grid grid-cols-3 md:grid-cols-6 gap-3">
                {assets?.colors.semantic && Object.entries(assets.colors.semantic).map(([name, color]) => (
                  <div key={name} className="text-center">
                    <div className="w-full aspect-square rounded-lg mb-2 border border-base-300" style={{ backgroundColor: color }} />
                    <div className="text-sm font-medium capitalize">{name}</div>
                    <code className="text-xs text-base-content/60">{color}</code>
                  </div>
                ))}
              </div>
            </div>

            {/* Text Colors */}
            {assets?.colors.text && (
              <div>
                <h4 className="text-sm font-medium mb-3">Text Colors</h4>
                <div className="grid grid-cols-3 md:grid-cols-6 gap-3">
                  {Object.entries(assets.colors.text).map(([name, color]) => (
                    <div key={name} className="text-center">
                      <div className="w-full aspect-square rounded-lg mb-2 border border-base-300" style={{ backgroundColor: color }} />
                      <div className="text-sm font-medium capitalize">{name}</div>
                      <code className="text-xs text-base-content/60">{color}</code>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Typography Section */}
      <div className="card bg-base-200">
        <div className="card-body">
          <h3 className="card-title text-lg">Typography System</h3>

          <div className="space-y-4 mt-4">
            {assets?.typography?.fonts && Object.entries(assets.typography.fonts).map(([role, font]) => (
              <div key={role} className="p-4 rounded-lg bg-base-100 border border-base-300">
                <div className="flex items-center gap-2 mb-4">
                  <Type size={20} className="text-primary" />
                  <h4 className="font-semibold capitalize">{role}</h4>
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
                    <span className="text-base-content/60">Source:</span>
                    <div className="badge badge-ghost badge-sm">{font.source}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

// ==================== VOICE PROFILE ====================

function VoiceProfileView() {
  const { data: voice, isLoading } = useBrandVoice();

  if (isLoading) {
    return <LoadingSpinner message="Loading voice profile..." />;
  }

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

  const formalityLabels: Record<number, string> = {
    1: 'Very Casual',
    2: 'Casual',
    3: 'Professional',
    4: 'Formal',
    5: 'Very Formal',
  };

  return (
    <div className="space-y-6">
      {/* Personality & Tone */}
      <div className="card bg-base-200">
        <div className="card-body">
          <h3 className="card-title text-lg">Personality & Tone</h3>

          <div className="space-y-6 mt-4">
            <div>
              <h4 className="text-sm font-medium mb-3">Personality Traits</h4>
              <div className="flex flex-wrap gap-2">
                {voice.personality?.map((trait: string) => (
                  <div key={trait} className="badge badge-accent badge-lg">{trait}</div>
                ))}
              </div>
            </div>

            <div className="flex flex-wrap gap-6">
              <div>
                <span className="text-sm text-base-content/60">Tone:</span>
                <div className="badge badge-ghost ml-2">{voice.tone}</div>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-sm text-base-content/60">Formality:</span>
                <div className="flex gap-1">
                  {[1, 2, 3, 4, 5].map(level => (
                    <div
                      key={level}
                      className={`w-8 h-8 rounded flex items-center justify-center text-sm font-medium ${
                        level === voice.formality_level
                          ? 'bg-primary text-primary-content'
                          : 'bg-base-300'
                      }`}
                    >
                      {level}
                    </div>
                  ))}
                </div>
                <span className="text-sm font-medium">{formalityLabels[voice.formality_level]}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Style Guidelines */}
      <div className="card bg-base-200">
        <div className="card-body">
          <h3 className="card-title text-lg">Style Guidelines</h3>

          <div className="grid md:grid-cols-2 gap-4 mt-4">
            <div className="p-4 rounded-lg bg-base-100">
              <div className="text-sm text-base-content/60 mb-2">Active Voice Target</div>
              <progress className="progress progress-primary w-full" value={voice.style.active_voice_target * 100} max="100"></progress>
              <div className="text-right text-sm mt-1">{Math.round(voice.style.active_voice_target * 100)}%</div>
            </div>
            <div className="p-4 rounded-lg bg-base-100">
              <div className="text-sm text-base-content/60 mb-2">Sentence Length</div>
              <div className="text-2xl font-bold">{voice.style.sentence_length_target}</div>
              <div className="text-xs text-base-content/60">words average</div>
            </div>
            <div className="p-4 rounded-lg bg-base-100">
              <div className="text-sm text-base-content/60 mb-2">Paragraph Max</div>
              <div className="text-2xl font-bold">{voice.style.paragraph_length_max}</div>
              <div className="text-xs text-base-content/60">sentences</div>
            </div>
            <div className="p-4 rounded-lg bg-base-100">
              <div className="text-sm text-base-content/60 mb-2">Contractions</div>
              <div className={`badge ${voice.style.use_contractions ? 'badge-success' : 'badge-ghost'}`}>
                {voice.style.use_contractions ? 'Allowed' : 'Avoid'}
              </div>
            </div>
          </div>

          <div className="mt-4">
            <div className="text-sm text-base-content/60 mb-2">Person Usage</div>
            <div className="flex gap-2">
              {voice.style.use_first_person && <div className="badge badge-info">First Person</div>}
              {voice.style.use_second_person && <div className="badge badge-info">Second Person</div>}
            </div>
          </div>
        </div>
      </div>

      {/* Overrides */}
      {((voice.available_doc_types?.length ?? 0) > 0 || (voice.available_audiences?.length ?? 0) > 0) && (
        <div className="card bg-base-200">
          <div className="card-body">
            <h3 className="card-title text-lg">Context Overrides</h3>

            <div className="grid md:grid-cols-2 gap-6 mt-4">
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
          </div>
        </div>
      )}

      {/* Terminology */}
      {((voice.preferred_terms?.length ?? 0) > 0 || (voice.avoid_phrases?.length ?? 0) > 0) && (
        <div className="card bg-base-200">
          <div className="card-body">
            <h3 className="card-title text-lg">Terminology Guidelines</h3>

            <div className="space-y-6 mt-4">
              {(voice.preferred_terms?.length ?? 0) > 0 && (
                <div>
                  <h4 className="font-medium mb-3">Preferred Terms</h4>
                  <div className="space-y-2">
                    {voice.preferred_terms?.slice(0, 5).map((term: { prefer: string; avoid: string[] }, i: number) => (
                      <div key={i} className="flex items-center gap-2 text-sm">
                        <div className="badge badge-success">{term.prefer}</div>
                        <span className="text-base-content/60">instead of</span>
                        <span className="text-base-content/80">{term.avoid.join(', ')}</span>
                      </div>
                    ))}
                    {(voice.preferred_terms?.length ?? 0) > 5 && (
                      <div className="text-sm text-base-content/60">+{(voice.preferred_terms?.length ?? 0) - 5} more</div>
                    )}
                  </div>
                </div>
              )}
              {(voice.avoid_phrases?.length ?? 0) > 0 && (
                <div>
                  <h4 className="font-medium mb-3">Phrases to Avoid</h4>
                  <div className="flex flex-wrap gap-2">
                    {voice.avoid_phrases?.slice(0, 8).map((phrase: string) => (
                      <div key={phrase} className="badge badge-warning">{phrase}</div>
                    ))}
                    {(voice.avoid_phrases?.length ?? 0) > 8 && (
                      <span className="text-sm text-base-content/60">+{(voice.avoid_phrases?.length ?? 0) - 8} more</span>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ==================== VOICE CHECK ====================

function VoiceCheckView() {
  const { data, isLoading } = useVoiceCheck();

  if (isLoading) {
    return <LoadingSpinner message="Checking documents against voice guidelines..." />;
  }

  if (!data) {
    return (
      <div className="card bg-base-200">
        <div className="card-body items-center text-center py-16">
          <AlertCircle size={48} className="text-base-content/30 mb-4" />
          <h3 className="text-lg font-semibold">No Voice Check Data</h3>
          <p className="text-base-content/60">Unable to load voice check results.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Summary */}
      <div className="card bg-base-200">
        <div className="card-body">
          <h3 className="card-title text-lg">Voice Compliance Summary</h3>

          <div className="grid grid-cols-3 gap-4 mt-4">
            <div className="text-center p-4 rounded-lg bg-base-100">
              <div className="text-3xl font-bold">{data.summary.pass_rate}%</div>
              <div className="text-sm text-base-content/60">Pass Rate</div>
            </div>
            <div className="text-center p-4 rounded-lg bg-base-100">
              <div className="text-3xl font-bold">{data.summary.documents_passed}/{data.summary.documents_checked}</div>
              <div className="text-sm text-base-content/60">Documents Passing</div>
            </div>
            <div className="text-center p-4 rounded-lg bg-base-100">
              <div className="text-3xl font-bold">{data.summary.total_issues}</div>
              <div className="text-sm text-base-content/60">Total Issues</div>
            </div>
          </div>

          <progress
            className={`progress w-full mt-4 ${
              data.summary.pass_rate >= 80 ? 'progress-success' :
              data.summary.pass_rate >= 50 ? 'progress-warning' : 'progress-error'
            }`}
            value={data.summary.pass_rate}
            max="100"
          ></progress>
        </div>
      </div>

      {/* Document Results */}
      <div className="card bg-base-200">
        <div className="card-body">
          <h3 className="card-title text-lg">Document Results</h3>

          <div className="space-y-3 mt-4">
            {data.results.map((result) => (
              <div
                key={result.document}
                className={`p-4 rounded-lg border ${
                  result.passed ? 'bg-success/5 border-success/20' : 'bg-warning/5 border-warning/20'
                }`}
              >
                <div className="flex items-center gap-3">
                  {result.passed ? (
                    <CheckCircle size={18} className="text-success" />
                  ) : (
                    <XCircle size={18} className="text-error" />
                  )}
                  <span className="font-medium flex-1">{result.document_name}</span>
                  <div className={`badge ${result.passed ? 'badge-success' : 'badge-warning'}`}>
                    {result.issues.length} issues
                  </div>
                </div>
                {result.issues.length > 0 && (
                  <div className="mt-3 pl-7 space-y-2">
                    {result.issues.map((issue, i) => (
                      <div key={i} className="flex items-start gap-2 text-sm">
                        <div className={`badge badge-sm ${
                          issue.severity === 'error' ? 'badge-error' :
                          issue.severity === 'warning' ? 'badge-warning' : 'badge-info'
                        }`}>
                          {issue.type}
                        </div>
                        <span className="text-base-content/80">{issue.message}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

// ==================== FILES ====================

function FilesView() {
  const { data, isLoading } = useBrandFiles();
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const { data: fileContent } = useBrandFile(selectedFile || '');

  if (isLoading) {
    return <LoadingSpinner message="Loading brand files..." />;
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
    <div className="space-y-6">
      {/* File Categories */}
      <div className="card bg-base-200">
        <div className="card-body">
          <h3 className="card-title text-lg">Brand Files</h3>

          <div className="flex flex-wrap gap-3 mt-4">
            {data?.categories && Object.entries(data.categories).map(([category, count]) => (
              count > 0 && (
                <div key={category} className="flex items-center gap-2 px-3 py-2 rounded-lg bg-base-100 border border-base-300">
                  {getCategoryIcon(category)}
                  <span className="capitalize">{category}</span>
                  <div className="badge badge-ghost badge-sm">{count}</div>
                </div>
              )
            ))}
          </div>
        </div>
      </div>

      {/* File List & Preview */}
      <div className="grid md:grid-cols-2 gap-6">
        <div className="card bg-base-200">
          <div className="card-body">
            <h3 className="card-title text-lg">Files ({data?.total || 0})</h3>

            <div className="space-y-2 mt-4 max-h-96 overflow-y-auto">
              {data?.files.map((file) => (
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
                    <div className="flex gap-1">
                      <div className="badge badge-ghost badge-xs">{file.type}</div>
                      {file.legacy && <div className="badge badge-warning badge-xs">legacy</div>}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="card bg-base-200">
          <div className="card-body">
            <h3 className="card-title text-lg">Preview</h3>

            <div className="mt-4">
              {selectedFile && fileContent ? (
                <div>
                  {fileContent.encoding === 'base64' && fileContent.mime_type.startsWith('image/') ? (
                    <img
                      src={`data:${fileContent.mime_type};base64,${fileContent.content}`}
                      alt={fileContent.name}
                      className="max-w-full rounded-lg"
                    />
                  ) : fileContent.encoding === 'text' ? (
                    <pre className="text-xs bg-base-300 p-4 rounded-lg overflow-auto max-h-80">{fileContent.content}</pre>
                  ) : (
                    <div className="text-center py-12">
                      <FileText size={48} className="text-base-content/30 mx-auto mb-3" />
                      <p className="text-base-content/60">Binary file - {fileContent.size} bytes</p>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-center py-12">
                  <Eye size={48} className="text-base-content/30 mx-auto mb-3" />
                  <p className="text-base-content/60">Select a file to preview</p>
                </div>
              )}
            </div>
          </div>
        </div>
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
    return <LoadingSpinner message="Loading brand notes..." />;
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

  const priorityColors: Record<string, string> = {
    low: 'badge-ghost',
    medium: 'badge-info',
    high: 'badge-warning',
    critical: 'badge-error',
  };

  return (
    <div className="space-y-6">
      {/* Add Note */}
      <div className="card bg-base-200">
        <div className="card-body">
          <div className="flex items-center justify-between">
            <h3 className="card-title text-lg">Brand Notes for AI Processing</h3>
            <button className="btn btn-primary btn-sm" onClick={() => setShowAddForm(!showAddForm)}>
              <Plus size={14} /> Add Note
            </button>
          </div>

          <p className="text-sm text-base-content/60 mt-2">
            Add notes about brand elements for AI to process. Notes can target specific files or general guidelines.
          </p>

          {showAddForm && (
            <div className="mt-4 p-4 rounded-lg bg-base-100 border border-base-300 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <select
                  value={newNote.category}
                  onChange={(e) => setNewNote({ ...newNote, category: e.target.value })}
                  className="select select-bordered w-full"
                >
                  {data?.categories.map(cat => (
                    <option key={cat} value={cat}>{cat}</option>
                  ))}
                </select>
                <select
                  value={newNote.priority}
                  onChange={(e) => setNewNote({ ...newNote, priority: e.target.value })}
                  className="select select-bordered w-full"
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
                className="textarea textarea-bordered w-full"
                rows={3}
              />
              <div className="flex justify-end gap-2">
                <button className="btn btn-ghost" onClick={() => setShowAddForm(false)}>Cancel</button>
                <button className="btn btn-primary" onClick={handleAddNote} disabled={!newNote.text.trim()}>
                  Add Note
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Pending Notes */}
      <div className="card bg-base-200">
        <div className="card-body">
          <h3 className="card-title text-lg">Pending Notes ({pendingNotes.length})</h3>

          {pendingNotes.length === 0 ? (
            <p className="text-base-content/60 mt-4">No pending notes</p>
          ) : (
            <div className="space-y-3 mt-4">
              {pendingNotes.map((note) => (
                <div key={note.id} className="p-4 rounded-lg bg-base-100 border border-base-300">
                  <div className="flex items-center gap-2 mb-2">
                    <div className={`badge ${priorityColors[note.priority]}`}>{note.priority}</div>
                    <div className="badge badge-ghost">{note.category}</div>
                    {note.target && <span className="text-xs text-base-content/50">{note.target}</span>}
                  </div>
                  <p className="text-sm">{note.text}</p>
                  <div className="flex gap-2 mt-3">
                    <button
                      className="btn btn-ghost btn-xs"
                      onClick={() => handleStatusChange(note.id, 'completed')}
                    >
                      <CheckCircle size={14} /> Complete
                    </button>
                    <button
                      className="btn btn-ghost btn-xs text-error"
                      onClick={() => handleDelete(note.id)}
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Completed Notes */}
      {completedNotes.length > 0 && (
        <div className="card bg-base-200">
          <div className="card-body">
            <h3 className="card-title text-lg">Completed ({completedNotes.length})</h3>

            <div className="space-y-3 mt-4 opacity-60">
              {completedNotes.slice(0, 5).map((note) => (
                <div key={note.id} className="p-4 rounded-lg bg-base-100 border border-base-300">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="badge badge-success">completed</div>
                    <div className="badge badge-ghost">{note.category}</div>
                  </div>
                  <p className="text-sm">{note.text}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ==================== HELPER COMPONENTS ====================

function LogoPreview({ path, alt }: { path: string; alt: string }) {
  const { data, isLoading } = useBrandFile(path);

  if (isLoading || !data) {
    return <span className="loading loading-spinner loading-sm"></span>;
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
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold mb-4">Brand Hub</h1>
        <SubTabs tabs={tabs} basePath="/brand" />
      </div>

      <Routes>
        <Route index element={<OverviewView />} />
        <Route path="identity" element={<VisualIdentityView />} />
        <Route path="voice" element={<VoiceProfileView />} />
        <Route path="check" element={<VoiceCheckView />} />
        <Route path="files" element={<FilesView />} />
        <Route path="notes" element={<NotesView />} />
      </Routes>
    </div>
  );
}
