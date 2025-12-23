import { useState } from 'react';
import { Routes, Route } from 'react-router-dom';
import { useBuildStatus, useBuild, useProject } from '@/hooks/useApi';
import { useQuery } from '@tanstack/react-query';
import { SubTabs } from '@/components/ui/SubTabs';
import {
  FileText,
  Presentation,
  Table,
  Film,
  CheckCircle,
  XCircle,
  Clock,
  Play,
  Palette,
  Type,
  Image
} from 'lucide-react';

const tabs = [
  { path: '', label: 'Build' },
  { path: 'brand', label: 'Brand' },
];

const formatIcons: Record<string, typeof FileText> = {
  html: FileText,
  pptx: Presentation,
  xlsx: Table,
  pdf: FileText,
  video: Film,
};

// Build View
function BuildView() {
  const { data: buildStatus, isLoading } = useBuildStatus();
  const { data: project } = useProject();
  const buildMutation = useBuild();

  const [selectedFormats, setSelectedFormats] = useState<string[]>(['html']);
  const [selectedLanguages, setSelectedLanguages] = useState<string[]>(['en']);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <span className="loading loading-spinner loading-lg text-primary"></span>
          <p className="mt-4 text-base-content/60">Loading build status...</p>
        </div>
      </div>
    );
  }

  const formats = buildStatus?.availableFormats ?? ['html', 'pptx', 'xlsx'];
  const languages = project?.languages ? Object.keys(project.languages) : ['en'];

  const toggleFormat = (format: string) => {
    setSelectedFormats(prev =>
      prev.includes(format)
        ? prev.filter(f => f !== format)
        : [...prev, format]
    );
  };

  const toggleLanguage = (lang: string) => {
    setSelectedLanguages(prev =>
      prev.includes(lang)
        ? prev.filter(l => l !== lang)
        : [...prev, lang]
    );
  };

  const handleBuild = () => {
    buildMutation.mutate({
      formats: selectedFormats,
      languages: selectedLanguages,
    });
  };

  return (
    <div className="space-y-6">
      {/* Build Status */}
      <div className="card bg-gradient-to-br from-base-200 to-base-300 border border-base-300">
        <div className="card-body">
          <div className="flex items-center gap-4">
            {buildStatus?.isBuilding ? (
              <>
                <span className="loading loading-spinner loading-lg text-primary"></span>
                <div>
                  <div className="font-semibold">Building...</div>
                  <div className="text-sm text-base-content/60">Please wait while your content is being processed</div>
                </div>
              </>
            ) : (
              <>
                {buildStatus?.lastBuildStatus === 'success' ? (
                  <CheckCircle size={48} className="text-success" />
                ) : buildStatus?.lastBuildStatus === 'failed' ? (
                  <XCircle size={48} className="text-error" />
                ) : (
                  <Clock size={48} className="text-base-content/40" />
                )}
                <div>
                  <div className="font-semibold">
                    {buildStatus?.lastBuildStatus === 'success' ? 'Last build successful' :
                     buildStatus?.lastBuildStatus === 'failed' ? 'Last build failed' :
                     'No recent builds'}
                  </div>
                  {buildStatus?.lastBuild && (
                    <div className="text-sm text-base-content/60">
                      {new Date(buildStatus.lastBuild).toLocaleString()}
                    </div>
                  )}
                </div>
              </>
            )}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Format Selection */}
        <div className="card bg-base-200">
          <div className="card-body">
            <h3 className="card-title text-lg">Output Formats</h3>
            <p className="text-sm text-base-content/60 mb-4">Select formats to generate</p>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              {formats.map(format => {
                const Icon = formatIcons[format] ?? FileText;
                const isSelected = selectedFormats.includes(format);
                return (
                  <button
                    key={format}
                    className={`flex flex-col items-center gap-2 p-4 rounded-lg transition-all ${
                      isSelected
                        ? 'bg-primary/20 border-2 border-primary'
                        : 'bg-base-300 border-2 border-transparent hover:bg-base-100'
                    }`}
                    onClick={() => toggleFormat(format)}
                  >
                    <Icon size={24} className={isSelected ? 'text-primary' : ''} />
                    <span className="font-medium text-sm">{format.toUpperCase()}</span>
                    {isSelected && <CheckCircle size={16} className="text-primary" />}
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        {/* Language Selection */}
        <div className="card bg-base-200">
          <div className="card-body">
            <h3 className="card-title text-lg">Languages</h3>
            <p className="text-sm text-base-content/60 mb-4">Select languages to build</p>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              {languages.map(lang => {
                const isSelected = selectedLanguages.includes(lang);
                return (
                  <button
                    key={lang}
                    className={`flex items-center justify-center gap-2 p-4 rounded-lg transition-all ${
                      isSelected
                        ? 'bg-success/20 border-2 border-success'
                        : 'bg-base-300 border-2 border-transparent hover:bg-base-100'
                    }`}
                    onClick={() => toggleLanguage(lang)}
                  >
                    <span className="font-semibold">{lang.toUpperCase()}</span>
                    {isSelected && <CheckCircle size={16} className="text-success" />}
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      </div>

      {/* Build Button */}
      <div className="card bg-base-200">
        <div className="card-body">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex flex-wrap items-center gap-6">
              <div className="flex items-center gap-2">
                <span className="text-sm text-base-content/60">Formats:</span>
                <div className="flex gap-1">
                  {selectedFormats.map(f => (
                    <div key={f} className="badge badge-primary">{f.toUpperCase()}</div>
                  ))}
                  {selectedFormats.length === 0 && <span className="text-sm text-base-content/50">None selected</span>}
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-sm text-base-content/60">Languages:</span>
                <div className="flex gap-1">
                  {selectedLanguages.map(l => (
                    <div key={l} className="badge badge-success">{l.toUpperCase()}</div>
                  ))}
                  {selectedLanguages.length === 0 && <span className="text-sm text-base-content/50">None selected</span>}
                </div>
              </div>
            </div>
            <button
              className="btn btn-primary btn-lg gap-2"
              onClick={handleBuild}
              disabled={buildMutation.isPending || selectedFormats.length === 0 || selectedLanguages.length === 0}
            >
              {buildMutation.isPending ? (
                <span className="loading loading-spinner"></span>
              ) : (
                <Play size={20} />
              )}
              Start Build
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// Brand View - shows brand/design system configuration
function BrandView() {
  const { data: project } = useProject();

  // Fetch brand configuration from API
  const { data: brandData, isLoading } = useQuery({
    queryKey: ['brand'],
    queryFn: async () => {
      const response = await fetch('/api/brand');
      if (!response.ok) {
        return null;
      }
      return response.json();
    },
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <span className="loading loading-spinner loading-lg text-primary"></span>
          <p className="mt-4 text-base-content/60">Loading brand configuration...</p>
        </div>
      </div>
    );
  }

  // Use project theme as fallback
  const colors = brandData?.colors || {
    primary: '#1a365d',
    secondary: '#2a4a7f',
    accent: '#3182ce',
  };

  const typography = brandData?.typography || {
    heading: 'Inter',
    body: 'Inter',
    code: 'JetBrains Mono',
  };

  const logos = brandData?.logos || {};

  return (
    <div className="space-y-6">
      {/* Brand Overview */}
      <div className="card bg-gradient-to-br from-base-200 to-base-300 border border-base-300">
        <div className="card-body">
          <div className="flex items-center gap-4">
            <Palette size={32} className="text-primary" />
            <div className="flex-1">
              <h2 className="text-xl font-semibold">{brandData?.name || project?.name || 'Project'}</h2>
              <p className="text-sm text-base-content/60">Brand & Design System</p>
            </div>
            {brandData?.source === 'brand.yaml' ? (
              <div className="badge badge-success">brand.yaml</div>
            ) : (
              <div className="badge badge-warning">theme.yaml (legacy)</div>
            )}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Colors */}
        <div className="card bg-base-200">
          <div className="card-body">
            <h3 className="card-title text-lg">Colors</h3>
            <p className="text-sm text-base-content/60 mb-4">Brand color palette</p>
            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-lg border border-base-300" style={{ backgroundColor: colors.primary }} />
                <div>
                  <div className="font-medium text-sm">Primary</div>
                  <code className="text-xs text-base-content/60">{colors.primary}</code>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-lg border border-base-300" style={{ backgroundColor: colors.secondary }} />
                <div>
                  <div className="font-medium text-sm">Secondary</div>
                  <code className="text-xs text-base-content/60">{colors.secondary}</code>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-lg border border-base-300" style={{ backgroundColor: colors.accent }} />
                <div>
                  <div className="font-medium text-sm">Accent</div>
                  <code className="text-xs text-base-content/60">{colors.accent}</code>
                </div>
              </div>
            </div>
            {brandData?.colors?.semantic && (
              <div className="mt-4 pt-4 border-t border-base-300">
                <h4 className="text-xs uppercase tracking-wider text-base-content/50 mb-3">Semantic Colors</h4>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(brandData.colors.semantic).map(([name, color]) => (
                    <div key={name} className="flex items-center gap-2">
                      <div className="w-6 h-6 rounded border border-base-300" style={{ backgroundColor: color as string }} />
                      <span className="text-xs">{name}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Typography */}
        <div className="card bg-base-200">
          <div className="card-body">
            <h3 className="card-title text-lg">Typography</h3>
            <p className="text-sm text-base-content/60 mb-4">Font families</p>
            <div className="space-y-3">
              <div className="flex items-center gap-3 p-3 rounded-lg bg-base-300">
                <Type size={20} className="text-base-content/60" />
                <div>
                  <div className="text-xs uppercase tracking-wider text-base-content/50">Heading</div>
                  <div className="font-medium" style={{ fontFamily: typography.heading }}>{typography.heading}</div>
                </div>
              </div>
              <div className="flex items-center gap-3 p-3 rounded-lg bg-base-300">
                <Type size={20} className="text-base-content/60" />
                <div>
                  <div className="text-xs uppercase tracking-wider text-base-content/50">Body</div>
                  <div className="font-medium" style={{ fontFamily: typography.body }}>{typography.body}</div>
                </div>
              </div>
              <div className="flex items-center gap-3 p-3 rounded-lg bg-base-300">
                <Type size={20} className="text-base-content/60" />
                <div>
                  <div className="text-xs uppercase tracking-wider text-base-content/50">Code</div>
                  <code className="font-medium" style={{ fontFamily: typography.code }}>{typography.code}</code>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Logos */}
        <div className="card bg-base-200">
          <div className="card-body">
            <h3 className="card-title text-lg">Logos</h3>
            <p className="text-sm text-base-content/60 mb-4">Brand assets</p>
            <div className="space-y-2">
              {Object.entries(logos).length > 0 ? (
                Object.entries(logos).map(([variant, logo]: [string, unknown]) => (
                  <div key={variant} className="flex items-center gap-3 p-2">
                    <Image size={16} className="text-base-content/60" />
                    <span className="flex-1 capitalize">{variant}</span>
                    {(logo as { exists?: boolean })?.exists ? (
                      <div className="badge badge-success badge-sm">Found</div>
                    ) : (
                      <div className="badge badge-ghost badge-sm">Not found</div>
                    )}
                  </div>
                ))
              ) : (
                <p className="text-sm text-base-content/60">No logos configured</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// Main Build Page
export function Build() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-semibold">Build</h1>
        <SubTabs tabs={tabs} basePath="/build" />
      </div>

      <Routes>
        <Route index element={<BuildView />} />
        <Route path="brand" element={<BrandView />} />
      </Routes>
    </div>
  );
}
