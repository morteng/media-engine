import { useState } from 'react';
import { useBuildStatus, useBuild, useProject } from '@/hooks/useApi';
import { Card, CardHeader, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { LoadingState, Spinner } from '@/components/ui/Spinner';
import {
  FileText,
  Presentation,
  Table,
  Film,
  CheckCircle,
  XCircle,
  Clock,
  Play
} from 'lucide-react';

const formatIcons: Record<string, typeof FileText> = {
  html: FileText,
  pptx: Presentation,
  xlsx: Table,
  pdf: FileText,
  video: Film,
};

export function Build() {
  const { data: buildStatus, isLoading } = useBuildStatus();
  const { data: project } = useProject();
  const buildMutation = useBuild();

  const [selectedFormats, setSelectedFormats] = useState<string[]>(['html']);
  const [selectedLanguages, setSelectedLanguages] = useState<string[]>(['en']);

  if (isLoading) {
    return <LoadingState message="Loading build status..." />;
  }

  const formats = buildStatus?.availableFormats ?? ['html', 'pptx', 'xlsx'];
  // languages is an object like {en: {...}, no: {...}}, so get the keys
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
    <div className="page build-page">
      <div className="page-header">
        <h1>Build</h1>
        <p className="text-muted">Generate outputs from your content</p>
      </div>

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
