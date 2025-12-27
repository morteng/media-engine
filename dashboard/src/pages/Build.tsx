import { useState, useEffect, useMemo } from 'react';
import {
  useBuildStatus,
  useBuildPublications,
  useBuildPresets,
  useUnifiedBuild,
  useCancelBuild,
  usePublishConfiguration,
  useBuildOutputs,
} from '@/hooks/useApi';
import { PublicationCard, OptionsPanel, ProgressSection } from '@/components/build';
import {
  FileText,
  Presentation,
  Table,
  Film,
  Play,
  StopCircle,
  RefreshCw,
  Package,
  CheckCircle,
  AlertCircle,
  Eye,
  FileDown,
} from 'lucide-react';
import type { UnifiedBuildPublication } from '@/api/types';

const formatIcons: Record<string, typeof FileText> = {
  html: FileText,
  pptx: Presentation,
  xlsx: Table,
  pdf: FileText,
  video: Film,
  mp4: Film,
};

const formatColors: Record<string, string> = {
  html: 'badge-info',
  pptx: 'badge-warning',
  xlsx: 'badge-success',
  pdf: 'badge-error',
  video: 'badge-secondary',
  mp4: 'badge-secondary',
};

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatTimeAgo(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffMins < 1) return 'just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString();
}

// State for each publication's build config
interface PublicationBuildState {
  selected: boolean;
  formats: string[];
  languages: string[];
}

export function Build() {
  const { data: buildStatus, refetch: refetchStatus } = useBuildStatus();
  const { data: publicationsData, isLoading: loadingPublications } = useBuildPublications();
  const { data: presetsData } = useBuildPresets();
  const { data: publishConfig } = usePublishConfiguration();
  const { data: buildOutputs } = useBuildOutputs();
  const buildMutation = useUnifiedBuild();
  const cancelMutation = useCancelBuild();

  // Build configuration state
  const [publicationStates, setPublicationStates] = useState<Record<string, PublicationBuildState>>({});
  const [outputDir, setOutputDir] = useState('');
  const [useDesktop, setUseDesktop] = useState(false);
  const [includeFonts, setIncludeFonts] = useState(true);
  const [includeDiagrams, setIncludeDiagrams] = useState(true);
  const [includeVideos, setIncludeVideos] = useState(true);
  const [includeNavigation, setIncludeNavigation] = useState(true);
  const [selectedPreset, setSelectedPreset] = useState<string | undefined>();

  const presets = presetsData?.presets || [];

  // Initialize publication states when data loads
  useEffect(() => {
    if (publicationsData?.publications && Object.keys(publicationStates).length === 0) {
      const initialStates: Record<string, PublicationBuildState> = {};
      publicationsData.publications.forEach((pub) => {
        initialStates[pub.key] = {
          selected: true, // Select all by default
          formats: [...pub.formats], // All formats enabled by default
          languages: [...pub.languages], // All languages enabled by default
        };
      });
      setPublicationStates(initialStates);
    }
  }, [publicationsData, publicationStates]);

  // Initialize output directory from publish config
  useEffect(() => {
    if (publishConfig && !outputDir) {
      setOutputDir(publishConfig.useDesktop ? publishConfig.desktopDir : publishConfig.defaultDir);
      setUseDesktop(publishConfig.useDesktop);
    }
  }, [publishConfig, outputDir]);

  const publications = publicationsData?.publications || [];
  const isActive = buildStatus?.active || false;
  const progress = buildStatus?.progress || 0;
  const logs = buildStatus?.logs || [];
  const outputs = buildOutputs?.outputs || [];

  // Toggle publication selection
  const togglePublication = (key: string) => {
    setPublicationStates((prev) => ({
      ...prev,
      [key]: {
        ...prev[key],
        selected: !prev[key]?.selected,
      },
    }));
  };

  // Toggle format for a publication
  const toggleFormat = (pubKey: string, format: string) => {
    setPublicationStates((prev) => {
      const state = prev[pubKey];
      if (!state) return prev;
      const formats = state.formats.includes(format)
        ? state.formats.filter((f) => f !== format)
        : [...state.formats, format];
      return {
        ...prev,
        [pubKey]: { ...state, formats },
      };
    });
  };

  // Toggle language for a publication
  const toggleLanguage = (pubKey: string, language: string) => {
    setPublicationStates((prev) => {
      const state = prev[pubKey];
      if (!state) return prev;
      const languages = state.languages.includes(language)
        ? state.languages.filter((l) => l !== language)
        : [...state.languages, language];
      return {
        ...prev,
        [pubKey]: { ...state, languages },
      };
    });
  };

  // Select/deselect all publications
  const selectAll = () => {
    setPublicationStates((prev) => {
      const newStates = { ...prev };
      Object.keys(newStates).forEach((key) => {
        newStates[key] = { ...newStates[key], selected: true };
      });
      return newStates;
    });
  };

  const deselectAll = () => {
    setPublicationStates((prev) => {
      const newStates = { ...prev };
      Object.keys(newStates).forEach((key) => {
        newStates[key] = { ...newStates[key], selected: false };
      });
      return newStates;
    });
  };

  // Build request data
  const selectedPublications = useMemo(() => {
    return Object.entries(publicationStates)
      .filter(([, state]) => state.selected && state.formats.length > 0 && state.languages.length > 0)
      .map(([key, state]): UnifiedBuildPublication => ({
        key,
        formats: state.formats,
        languages: state.languages,
      }));
  }, [publicationStates]);

  const canBuild = selectedPublications.length > 0 && !isActive;

  // Handle build
  const handleBuild = (publish: boolean) => {
    buildMutation.mutate(
      {
        publications: selectedPublications,
        outputDir: outputDir,
        includeFonts,
        includeDiagrams,
        includeVideos,
        includeNavigation,
        publish,
        preset: selectedPreset,
      },
      {
        onSuccess: () => {
          refetchStatus();
        },
      }
    );
  };

  // Summary stats
  const selectedCount = Object.values(publicationStates).filter((s) => s.selected).length;
  const totalFormats = new Set(
    Object.values(publicationStates)
      .filter((s) => s.selected)
      .flatMap((s) => s.formats)
  );
  const totalLanguages = new Set(
    Object.values(publicationStates)
      .filter((s) => s.selected)
      .flatMap((s) => s.languages)
  );

  if (loadingPublications) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <span className="loading loading-spinner loading-lg text-primary"></span>
          <p className="mt-4 text-base-content/60">Loading publications...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Build & Publish</h1>
        <button className="btn btn-ghost btn-sm" onClick={() => refetchStatus()}>
          <RefreshCw size={16} />
        </button>
      </div>

      {/* Main Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Publications Panel - 2/3 width */}
        <div className="lg:col-span-2 space-y-4">
          {/* Publications Header */}
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-medium">Publications</h2>
            <div className="flex gap-2">
              <button className="btn btn-ghost btn-xs" onClick={selectAll} disabled={isActive}>
                Select All
              </button>
              <button className="btn btn-ghost btn-xs" onClick={deselectAll} disabled={isActive}>
                Clear
              </button>
            </div>
          </div>

          {/* Publications Grid */}
          {publications.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {publications.map((pub) => (
                <PublicationCard
                  key={pub.key}
                  publication={pub}
                  selected={publicationStates[pub.key]?.selected || false}
                  selectedFormats={publicationStates[pub.key]?.formats || []}
                  selectedLanguages={publicationStates[pub.key]?.languages || []}
                  onToggleSelect={() => togglePublication(pub.key)}
                  onToggleFormat={(format) => toggleFormat(pub.key, format)}
                  onToggleLanguage={(lang) => toggleLanguage(pub.key, lang)}
                  disabled={isActive}
                />
              ))}
            </div>
          ) : (
            <div className="card bg-base-200">
              <div className="card-body text-center py-12">
                <Package size={48} className="mx-auto text-base-content/30" />
                <p className="text-base-content/60 mt-4">No publications found</p>
                <p className="text-sm text-base-content/40">
                  Create publications in your project to build outputs
                </p>
              </div>
            </div>
          )}

          {/* Progress Section */}
          <ProgressSection active={isActive} progress={progress} logs={logs} />

          {/* Recent Outputs */}
          {outputs.length > 0 && !isActive && (
            <div className="card bg-base-200">
              <div className="card-body">
                <h3 className="font-medium mb-4">Recent Outputs</h3>
                <div className="overflow-x-auto">
                  <table className="table table-sm">
                    <thead>
                      <tr>
                        <th>File</th>
                        <th>Format</th>
                        <th>Lang</th>
                        <th>Size</th>
                        <th>Modified</th>
                        <th></th>
                      </tr>
                    </thead>
                    <tbody>
                      {outputs.slice(0, 8).map((output, idx) => {
                        const Icon = formatIcons[output.format.toLowerCase()] ?? FileText;
                        return (
                          <tr key={idx} className="hover">
                            <td className="flex items-center gap-2">
                              <Icon size={14} className="text-base-content/60" />
                              <span className="font-medium text-sm truncate max-w-[150px]">
                                {output.name}
                              </span>
                            </td>
                            <td>
                              <div
                                className={`badge badge-xs ${
                                  formatColors[output.format.toLowerCase()] || 'badge-ghost'
                                }`}
                              >
                                {output.format}
                              </div>
                            </td>
                            <td>
                              <span className="text-xs">{output.language.toUpperCase()}</span>
                            </td>
                            <td className="text-xs text-base-content/60">
                              {formatFileSize(output.size)}
                            </td>
                            <td className="text-xs text-base-content/60">
                              {formatTimeAgo(output.modified)}
                            </td>
                            <td>
                              <div className="flex gap-1">
                                <button className="btn btn-ghost btn-xs" title="Preview">
                                  <Eye size={12} />
                                </button>
                                <a
                                  href={`/api/file?path=${encodeURIComponent(output.path)}`}
                                  className="btn btn-ghost btn-xs"
                                  title="Download"
                                  download
                                >
                                  <FileDown size={12} />
                                </a>
                              </div>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Options Panel - 1/3 width */}
        <div className="space-y-4">
          <OptionsPanel
            outputDir={outputDir}
            desktopPath={publishConfig?.desktopDir || '~/Desktop'}
            defaultPath={publishConfig?.defaultDir || 'dist'}
            useDesktop={useDesktop}
            includeFonts={includeFonts}
            includeDiagrams={includeDiagrams}
            includeVideos={includeVideos}
            includeNavigation={includeNavigation}
            preset={selectedPreset}
            presets={presets}
            onPresetChange={setSelectedPreset}
            onOutputDirChange={setOutputDir}
            onUseDesktopChange={setUseDesktop}
            onIncludeFontsChange={setIncludeFonts}
            onIncludeDiagramsChange={setIncludeDiagrams}
            onIncludeVideosChange={setIncludeVideos}
            onIncludeNavigationChange={setIncludeNavigation}
            disabled={isActive}
          />

          {/* Selection Summary */}
          <div className="card bg-base-200">
            <div className="card-body py-4">
              <div className="text-sm text-base-content/60 space-y-1">
                <div className="flex justify-between">
                  <span>Publications:</span>
                  <span className="font-medium text-base-content">{selectedCount}</span>
                </div>
                <div className="flex justify-between">
                  <span>Formats:</span>
                  <span className="font-medium text-base-content">{totalFormats.size}</span>
                </div>
                <div className="flex justify-between">
                  <span>Languages:</span>
                  <span className="font-medium text-base-content">{totalLanguages.size}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="space-y-2">
            {isActive ? (
              <button
                className="btn btn-error w-full gap-2"
                onClick={() => cancelMutation.mutate()}
                disabled={cancelMutation.isPending}
              >
                {cancelMutation.isPending ? (
                  <span className="loading loading-spinner loading-sm"></span>
                ) : (
                  <StopCircle size={18} />
                )}
                Cancel Build
              </button>
            ) : (
              <>
                <button
                  className="btn btn-primary w-full gap-2"
                  onClick={() => handleBuild(true)}
                  disabled={!canBuild || buildMutation.isPending}
                >
                  {buildMutation.isPending ? (
                    <span className="loading loading-spinner loading-sm"></span>
                  ) : (
                    <Play size={18} />
                  )}
                  Build & Publish
                </button>
                <button
                  className="btn btn-ghost w-full gap-2 text-sm"
                  onClick={() => handleBuild(false)}
                  disabled={!canBuild || buildMutation.isPending}
                >
                  Build Only
                </button>
              </>
            )}
          </div>

          {/* Build Status */}
          {buildStatus?.last_build && !isActive && (
            <div className="flex items-center gap-2 text-sm text-base-content/60 justify-center">
              <CheckCircle size={14} className="text-success" />
              Last build: {formatTimeAgo(buildStatus.last_build)}
            </div>
          )}

          {/* Freshness Warning */}
          {buildStatus?.freshness_warning && !isActive && (
            <div className="alert alert-warning text-sm py-2">
              <AlertCircle size={16} />
              <span>{buildStatus.freshness_warning.message}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
