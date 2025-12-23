import { useState } from 'react';
import { Routes, Route } from 'react-router-dom';
import { useBuildStatus, useBuild, useProject } from '@/hooks/useApi';
import { useQuery } from '@tanstack/react-query';
import { Card, CardHeader, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { LoadingState, Spinner } from '@/components/ui/Spinner';
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
    return <LoadingState message="Loading build status..." />;
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
    <div className="build-content">
      {/* Build Status */}
      <Card className="build-status-card">
        <CardContent>
          <div className="build-status">
            {buildStatus?.isBuilding ? (
              <>
                <Spinner size="lg" />
                <div className="status-info">
                  <span className="status-label">Building...</span>
                  <span className="text-muted">Please wait while your content is being processed</span>
                </div>
              </>
            ) : (
              <>
                {buildStatus?.lastBuildStatus === 'success' ? (
                  <CheckCircle size={48} className="text-success" />
                ) : buildStatus?.lastBuildStatus === 'failed' ? (
                  <XCircle size={48} className="text-error" />
                ) : (
                  <Clock size={48} className="text-muted" />
                )}
                <div className="status-info">
                  <span className="status-label">
                    {buildStatus?.lastBuildStatus === 'success' ? 'Last build successful' :
                     buildStatus?.lastBuildStatus === 'failed' ? 'Last build failed' :
                     'No recent builds'}
                  </span>
                  {buildStatus?.lastBuild && (
                    <span className="text-muted">
                      {new Date(buildStatus.lastBuild).toLocaleString()}
                    </span>
                  )}
                </div>
              </>
            )}
          </div>
        </CardContent>
      </Card>

      <div className="build-options">
        {/* Format Selection */}
        <Card>
          <CardHeader title="Output Formats" subtitle="Select formats to generate" />
          <CardContent>
            <div className="format-grid">
              {formats.map(format => {
                const Icon = formatIcons[format] ?? FileText;
                const isSelected = selectedFormats.includes(format);
                return (
                  <button
                    key={format}
                    className={`format-option ${isSelected ? 'selected' : ''}`}
                    onClick={() => toggleFormat(format)}
                  >
                    <Icon size={24} />
                    <span className="format-name">{format.toUpperCase()}</span>
                    {isSelected && <CheckCircle size={16} className="check-icon" />}
                  </button>
                );
              })}
            </div>
          </CardContent>
        </Card>

        {/* Language Selection */}
        <Card>
          <CardHeader title="Languages" subtitle="Select languages to build" />
          <CardContent>
            <div className="language-grid">
              {languages.map(lang => {
                const isSelected = selectedLanguages.includes(lang);
                return (
                  <button
                    key={lang}
                    className={`language-option ${isSelected ? 'selected' : ''}`}
                    onClick={() => toggleLanguage(lang)}
                  >
                    <span className="lang-code">{lang.toUpperCase()}</span>
                    {isSelected && <CheckCircle size={16} className="check-icon" />}
                  </button>
                );
              })}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Build Button */}
      <Card className="build-action-card">
        <CardContent>
          <div className="build-summary">
            <div className="summary-item">
              <span className="label">Formats:</span>
              <div className="badges">
                {selectedFormats.map(f => (
                  <Badge key={f} variant="accent">{f.toUpperCase()}</Badge>
                ))}
              </div>
            </div>
            <div className="summary-item">
              <span className="label">Languages:</span>
              <div className="badges">
                {selectedLanguages.map(l => (
                  <Badge key={l} variant="success">{l.toUpperCase()}</Badge>
                ))}
              </div>
            </div>
          </div>
          <Button
            variant="primary"
            size="lg"
            onClick={handleBuild}
            loading={buildMutation.isPending}
            disabled={selectedFormats.length === 0 || selectedLanguages.length === 0}
          >
            <Play size={20} />
            Start Build
          </Button>
        </CardContent>
      </Card>
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
        // Return default if no brand endpoint yet
        return null;
      }
      return response.json();
    },
  });

  if (isLoading) {
    return <LoadingState message="Loading brand configuration..." />;
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
    <div className="brand-content">
      {/* Brand Overview */}
      <Card variant="gradient">
        <CardContent>
          <div className="brand-header">
            <Palette size={32} />
            <div>
              <h2>{brandData?.name || project?.name || 'Project'}</h2>
              <p className="text-muted">Brand & Design System</p>
            </div>
            {brandData?.source === 'brand.yaml' ? (
              <Badge variant="success">brand.yaml</Badge>
            ) : (
              <Badge variant="warning">theme.yaml (legacy)</Badge>
            )}
          </div>
        </CardContent>
      </Card>

      <div className="brand-grid">
        {/* Colors */}
        <Card>
          <CardHeader title="Colors" subtitle="Brand color palette" />
          <CardContent>
            <div className="color-swatches">
              <div className="color-swatch">
                <div className="swatch" style={{ backgroundColor: colors.primary }} />
                <div className="swatch-info">
                  <span className="swatch-label">Primary</span>
                  <code>{colors.primary}</code>
                </div>
              </div>
              <div className="color-swatch">
                <div className="swatch" style={{ backgroundColor: colors.secondary }} />
                <div className="swatch-info">
                  <span className="swatch-label">Secondary</span>
                  <code>{colors.secondary}</code>
                </div>
              </div>
              <div className="color-swatch">
                <div className="swatch" style={{ backgroundColor: colors.accent }} />
                <div className="swatch-info">
                  <span className="swatch-label">Accent</span>
                  <code>{colors.accent}</code>
                </div>
              </div>
            </div>
            {brandData?.colors?.semantic && (
              <div className="semantic-colors">
                <h4>Semantic Colors</h4>
                <div className="color-swatches small">
                  {Object.entries(brandData.colors.semantic).map(([name, color]) => (
                    <div key={name} className="color-swatch">
                      <div className="swatch small" style={{ backgroundColor: color as string }} />
                      <span className="swatch-label">{name}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Typography */}
        <Card>
          <CardHeader title="Typography" subtitle="Font families" />
          <CardContent>
            <div className="typography-list">
              <div className="font-item">
                <Type size={20} />
                <div className="font-info">
                  <span className="font-role">Heading</span>
                  <span className="font-family" style={{ fontFamily: typography.heading }}>
                    {typography.heading}
                  </span>
                </div>
              </div>
              <div className="font-item">
                <Type size={20} />
                <div className="font-info">
                  <span className="font-role">Body</span>
                  <span className="font-family" style={{ fontFamily: typography.body }}>
                    {typography.body}
                  </span>
                </div>
              </div>
              <div className="font-item">
                <Type size={20} />
                <div className="font-info">
                  <span className="font-role">Code</span>
                  <code className="font-family" style={{ fontFamily: typography.code }}>
                    {typography.code}
                  </code>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Logos */}
        <Card>
          <CardHeader title="Logos" subtitle="Brand assets" />
          <CardContent>
            <div className="logo-list">
              {Object.entries(logos).length > 0 ? (
                Object.entries(logos).map(([variant, logo]: [string, unknown]) => (
                  <div key={variant} className="logo-item">
                    <Image size={16} />
                    <span className="logo-variant">{variant}</span>
                    {(logo as { exists?: boolean })?.exists ? (
                      <Badge variant="success" size="sm">Found</Badge>
                    ) : (
                      <Badge variant="default" size="sm">Not found</Badge>
                    )}
                  </div>
                ))
              ) : (
                <p className="text-muted">No logos configured</p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      <style>{`
        .brand-content {
          display: flex;
          flex-direction: column;
          gap: 1.5rem;
        }

        .brand-header {
          display: flex;
          align-items: center;
          gap: 1rem;
        }

        .brand-header h2 {
          margin: 0;
        }

        .brand-header > :last-child {
          margin-left: auto;
        }

        .brand-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
          gap: 1.5rem;
        }

        .color-swatches {
          display: flex;
          flex-direction: column;
          gap: 0.75rem;
        }

        .color-swatches.small {
          flex-direction: row;
          flex-wrap: wrap;
          gap: 0.5rem;
        }

        .color-swatch {
          display: flex;
          align-items: center;
          gap: 0.75rem;
        }

        .swatch {
          width: 48px;
          height: 48px;
          border-radius: 8px;
          border: 1px solid var(--border);
        }

        .swatch.small {
          width: 24px;
          height: 24px;
          border-radius: 4px;
        }

        .swatch-info {
          display: flex;
          flex-direction: column;
          gap: 0.25rem;
        }

        .swatch-label {
          font-weight: 500;
          font-size: 0.875rem;
        }

        .swatch-info code {
          font-size: 0.75rem;
          color: var(--text-secondary);
        }

        .semantic-colors {
          margin-top: 1.5rem;
          padding-top: 1rem;
          border-top: 1px solid var(--border);
        }

        .semantic-colors h4 {
          margin: 0 0 0.75rem 0;
          font-size: 0.75rem;
          text-transform: uppercase;
          letter-spacing: 0.05em;
          color: var(--text-secondary);
        }

        .typography-list {
          display: flex;
          flex-direction: column;
          gap: 1rem;
        }

        .font-item {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          padding: 0.75rem;
          background: var(--bg-tertiary);
          border-radius: 8px;
        }

        .font-info {
          display: flex;
          flex-direction: column;
          gap: 0.25rem;
        }

        .font-role {
          font-size: 0.75rem;
          color: var(--text-secondary);
          text-transform: uppercase;
          letter-spacing: 0.05em;
        }

        .font-family {
          font-size: 1rem;
          font-weight: 500;
        }

        .logo-list {
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
        }

        .logo-item {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          padding: 0.5rem 0;
        }

        .logo-variant {
          flex: 1;
          text-transform: capitalize;
        }
      `}</style>
    </div>
  );
}

// Main Build Page
export function Build() {
  return (
    <div className="page build-page">
      <div className="page-header">
        <h1>Build</h1>
        <SubTabs tabs={tabs} basePath="/build" />
      </div>

      <Routes>
        <Route index element={<BuildView />} />
        <Route path="brand" element={<BrandView />} />
      </Routes>
    </div>
  );
}
