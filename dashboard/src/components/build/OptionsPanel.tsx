import { FolderOpen, Monitor, Type, Image, Film, Navigation, Layout } from 'lucide-react';

export interface LayoutPreset {
  name: string;
  description: string;
  template: string;
  formats: string[];
  features: Record<string, boolean>;
  maxWidth: string;
  fontScale: number;
  lineHeight: number;
}

interface OptionsPanelProps {
  outputDir: string;
  desktopPath: string;
  defaultPath: string;
  useDesktop: boolean;
  includeFonts: boolean;
  includeDiagrams: boolean;
  includeVideos: boolean;
  includeNavigation: boolean;
  // New preset support
  preset?: string;
  presets?: LayoutPreset[];
  onPresetChange?: (preset: string | undefined) => void;
  onOutputDirChange: (path: string) => void;
  onUseDesktopChange: (use: boolean) => void;
  onIncludeFontsChange: (include: boolean) => void;
  onIncludeDiagramsChange: (include: boolean) => void;
  onIncludeVideosChange: (include: boolean) => void;
  onIncludeNavigationChange: (include: boolean) => void;
  disabled?: boolean;
}

export function OptionsPanel({
  outputDir,
  desktopPath,
  defaultPath,
  useDesktop,
  includeFonts,
  includeDiagrams,
  includeVideos,
  includeNavigation,
  preset,
  presets = [],
  onPresetChange,
  onOutputDirChange,
  onUseDesktopChange,
  onIncludeFontsChange,
  onIncludeDiagramsChange,
  onIncludeVideosChange,
  onIncludeNavigationChange,
  disabled = false,
}: OptionsPanelProps) {
  const handleDesktopToggle = () => {
    const newUseDesktop = !useDesktop;
    onUseDesktopChange(newUseDesktop);
    onOutputDirChange(newUseDesktop ? desktopPath : defaultPath);
  };

  return (
    <div className="card bg-base-200">
      <div className="card-body">
        <h3 className="card-title text-lg">
          <FolderOpen size={20} />
          Output Options
        </h3>

        {/* Layout Preset Selection */}
        {presets.length > 0 && onPresetChange && (
          <>
            <div className="form-control mt-4">
              <label className="label">
                <span className="label-text flex items-center gap-2">
                  <Layout size={14} />
                  HTML Layout Preset
                </span>
              </label>
              <select
                className="select select-bordered select-sm w-full"
                value={preset || ''}
                onChange={(e) => onPresetChange(e.target.value || undefined)}
                disabled={disabled}
              >
                <option value="">Default (minimal)</option>
                {presets.map((p) => (
                  <option key={p.name} value={p.name}>
                    {p.name.charAt(0).toUpperCase() + p.name.slice(1)}
                  </option>
                ))}
              </select>
              {preset && presets.find((p) => p.name === preset) && (
                <label className="label">
                  <span className="label-text-alt text-base-content/50">
                    {presets.find((p) => p.name === preset)?.description}
                  </span>
                </label>
              )}
            </div>
            <div className="divider text-xs text-base-content/50 my-2"></div>
          </>
        )}

        {/* Output Directory */}
        <div className="form-control mt-4">
          <label className="label">
            <span className="label-text">Output Directory</span>
          </label>
          <input
            type="text"
            className="input input-bordered w-full text-sm"
            value={outputDir}
            onChange={(e) => {
              onOutputDirChange(e.target.value);
              onUseDesktopChange(false);
            }}
            placeholder={defaultPath}
            disabled={disabled}
          />
        </div>

        {/* Quick Path Buttons */}
        <div className="flex gap-2 mt-2">
          <button
            className={`btn btn-xs ${!useDesktop ? 'btn-primary' : 'btn-ghost'}`}
            onClick={() => {
              onOutputDirChange(defaultPath);
              onUseDesktopChange(false);
            }}
            disabled={disabled}
          >
            Default
          </button>
          <button
            className={`btn btn-xs gap-1 ${useDesktop ? 'btn-primary' : 'btn-ghost'}`}
            onClick={handleDesktopToggle}
            disabled={disabled}
          >
            <Monitor size={12} />
            Desktop
          </button>
        </div>

        {/* Include Options */}
        <div className="divider text-xs text-base-content/50">Include</div>

        <div className="grid grid-cols-2 gap-3">
          <label
            className={`flex items-center gap-2 p-2 rounded-lg cursor-pointer transition-all ${
              includeFonts ? 'bg-primary/10' : 'bg-base-300'
            }`}
          >
            <input
              type="checkbox"
              className="checkbox checkbox-primary checkbox-sm"
              checked={includeFonts}
              onChange={(e) => onIncludeFontsChange(e.target.checked)}
              disabled={disabled}
            />
            <Type size={16} className="text-base-content/60" />
            <span className="text-sm">Fonts</span>
          </label>

          <label
            className={`flex items-center gap-2 p-2 rounded-lg cursor-pointer transition-all ${
              includeDiagrams ? 'bg-primary/10' : 'bg-base-300'
            }`}
          >
            <input
              type="checkbox"
              className="checkbox checkbox-primary checkbox-sm"
              checked={includeDiagrams}
              onChange={(e) => onIncludeDiagramsChange(e.target.checked)}
              disabled={disabled}
            />
            <Image size={16} className="text-base-content/60" />
            <span className="text-sm">Diagrams</span>
          </label>

          <label
            className={`flex items-center gap-2 p-2 rounded-lg cursor-pointer transition-all ${
              includeVideos ? 'bg-primary/10' : 'bg-base-300'
            }`}
          >
            <input
              type="checkbox"
              className="checkbox checkbox-primary checkbox-sm"
              checked={includeVideos}
              onChange={(e) => onIncludeVideosChange(e.target.checked)}
              disabled={disabled}
            />
            <Film size={16} className="text-base-content/60" />
            <span className="text-sm">Videos</span>
          </label>

          <label
            className={`flex items-center gap-2 p-2 rounded-lg cursor-pointer transition-all ${
              includeNavigation ? 'bg-primary/10' : 'bg-base-300'
            }`}
          >
            <input
              type="checkbox"
              className="checkbox checkbox-primary checkbox-sm"
              checked={includeNavigation}
              onChange={(e) => onIncludeNavigationChange(e.target.checked)}
              disabled={disabled}
            />
            <Navigation size={16} className="text-base-content/60" />
            <span className="text-sm">Navigation</span>
          </label>
        </div>
      </div>
    </div>
  );
}
