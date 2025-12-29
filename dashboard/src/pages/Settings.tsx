import { useState, useMemo } from 'react';
import { useSettings as useSettingsContext, type Theme } from '@/contexts';
import {
  useSettings,
  useSettingsDefaults,
  useUpdateSettings,
} from '@/hooks/useApi';
import { ExpandableSection, Spinner } from '@/components/ui';
import { SettingField, SettingsSection } from '@/components/settings';
import { InfoTooltip } from '@/components/ui/InfoTooltip';
import type { SettingValue } from '@/api/types';
import {
  Moon,
  Sun,
  RotateCcw,
  Monitor,
  Folder,
  Video,
  Mic,
  Shield,
  Terminal,
  Clock,
  CheckCircle,
  AlertCircle,
  Settings2,
  Palette,
  Info,
} from 'lucide-react';

const themes: { id: Theme; label: string; description: string; icon: typeof Sun }[] = [
  {
    id: 'nord',
    label: 'Nord Light',
    description: 'Clean, light theme with soft colors',
    icon: Sun,
  },
  {
    id: 'sunset',
    label: 'Sunset Dark',
    description: 'Dark theme with warm undertones',
    icon: Moon,
  },
];

// Main Settings Page - Single page with expandable sections
export function Settings() {
  const { settings: localSettings, setTheme, updateSetting, resetSettings } = useSettingsContext();
  const { data: apiSettings, isLoading: apiLoading, error: apiError } = useSettings();
  const { data: defaults, isLoading: defaultsLoading } = useSettingsDefaults();
  const updateMutation = useUpdateSettings();

  // State for tracking changes in different sections
  const [projectChanges, setProjectChanges] = useState<Record<string, unknown>>({});
  const [qualityChanges, setQualityChanges] = useState<Record<string, unknown>>({});
  const [videoChanges, setVideoChanges] = useState<Record<string, unknown>>({});
  const [voiceoverChanges, setVoiceoverChanges] = useState<Record<string, unknown>>({});
  const [pathsChanges, setPathsChanges] = useState<Record<string, unknown>>({});

  // Group environment variables by category
  const envGroups = useMemo(() => {
    if (!apiSettings?.environment) return {};
    const groups: Record<string, Record<string, SettingValue>> = {};
    Object.entries(apiSettings.environment).forEach(([key, setting]) => {
      const prefix = key.split('_')[0];
      const category = prefix === 'ELEVENLABS' || prefix === 'OPENAI' || prefix === 'ANTHROPIC'
        ? 'API Keys'
        : prefix === 'MEDIA' ? 'Media Engine' : 'Other';
      if (!groups[category]) groups[category] = {};
      groups[category][key] = setting;
    });
    return groups;
  }, [apiSettings?.environment]);

  // Save handlers
  const handleProjectSave = async () => {
    try {
      await updateMutation.mutateAsync({ section: 'project', updates: projectChanges });
      setProjectChanges({});
    } catch (err) {
      console.error('Failed to save project settings:', err);
    }
  };

  const handleQualitySave = async () => {
    try {
      await updateMutation.mutateAsync({ section: 'quality', updates: qualityChanges });
      setQualityChanges({});
    } catch (err) {
      console.error('Failed to save quality settings:', err);
    }
  };

  const handleVideoSave = async () => {
    try {
      await updateMutation.mutateAsync({ section: 'video', updates: videoChanges });
      setVideoChanges({});
    } catch (err) {
      console.error('Failed to save video settings:', err);
    }
  };

  const handleVoiceoverSave = async () => {
    try {
      await updateMutation.mutateAsync({ section: 'voiceover', updates: voiceoverChanges });
      setVoiceoverChanges({});
    } catch (err) {
      console.error('Failed to save voiceover settings:', err);
    }
  };

  const handlePathsSave = async () => {
    try {
      await updateMutation.mutateAsync({ section: 'paths', updates: pathsChanges });
      setPathsChanges({});
    } catch (err) {
      console.error('Failed to save paths settings:', err);
    }
  };

  // Dropdown options
  const readingLevelOptions = [
    { value: 'elementary', label: 'Elementary (Grade 1-5)' },
    { value: 'middle_school', label: 'Middle School (Grade 6-8)' },
    { value: 'high_school', label: 'High School (Grade 9-12)' },
    { value: 'college', label: 'College' },
    { value: 'graduate', label: 'Graduate' },
  ];

  const lixLevelOptions = [
    { value: 'very_easy', label: 'Very Easy (LIX < 25)' },
    { value: 'easy', label: 'Easy (LIX 25-35)' },
    { value: 'medium', label: 'Medium (LIX 35-45)' },
    { value: 'difficult', label: 'Difficult (LIX 45-55)' },
    { value: 'very_difficult', label: 'Very Difficult (LIX > 55)' },
  ];

  const fpsOptions = [
    { value: '24', label: '24 fps' },
    { value: '30', label: '30 fps' },
    { value: '60', label: '60 fps' },
  ];

  const providerOptions = [
    { value: 'elevenlabs', label: 'ElevenLabs' },
    { value: 'openai', label: 'OpenAI' },
    { value: 'local', label: 'Local' },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold">Settings</h1>
          <p className="text-base-content/60 mt-1">Configure dashboard and project preferences</p>
        </div>
        <button className="btn btn-ghost btn-sm gap-2" onClick={resetSettings}>
          <RotateCcw size={16} />
          Reset Dashboard
        </button>
      </div>

      {/* Dashboard Settings (localStorage) */}
      <ExpandableSection
        title="Appearance"
        description="Theme and display preferences"
        icon={<Palette size={20} />}
        tooltip={{
          title: 'Appearance Settings',
          content: 'Visual preferences stored locally in your browser. These settings persist across sessions but are not shared with other users.',
        }}
        defaultExpanded
      >
        <div className="space-y-6">
          {/* Theme Selector */}
          <div>
            <h4 className="text-sm font-medium mb-3 flex items-center gap-2">
              Theme
              <InfoTooltip
                title="Theme Selection"
                content="Choose between light and dark themes. The theme affects all dashboard pages and is stored in your browser."
              />
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {themes.map((theme) => {
                const Icon = theme.icon;
                const isSelected = localSettings.theme === theme.id;
                return (
                  <button
                    key={theme.id}
                    className={`flex items-start gap-4 p-4 rounded-lg border-2 transition-all text-left ${
                      isSelected
                        ? 'border-primary bg-primary/10'
                        : 'border-base-300 hover:border-primary/50 hover:bg-base-300/50'
                    }`}
                    onClick={() => setTheme(theme.id)}
                  >
                    <div className={`p-2 rounded-lg ${isSelected ? 'bg-primary text-primary-content' : 'bg-base-300'}`}>
                      <Icon size={24} />
                    </div>
                    <div className="flex-1">
                      <div className="font-medium">{theme.label}</div>
                      <div className="text-sm text-base-content/60">{theme.description}</div>
                    </div>
                    {isSelected && <div className="badge badge-primary badge-sm">Active</div>}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Dashboard Options */}
          <div className="space-y-4">
            <div className="flex items-center justify-between p-3 rounded-lg bg-base-300/50">
              <div className="flex items-center gap-3">
                <Monitor size={18} className="text-base-content/60" />
                <div>
                  <div className="font-medium text-sm">Compact Mode</div>
                  <div className="text-xs text-base-content/60">Use smaller spacing and fonts</div>
                </div>
              </div>
              <input
                type="checkbox"
                className="toggle toggle-primary toggle-sm"
                checked={localSettings.compactMode}
                onChange={(e) => updateSetting('compactMode', e.target.checked)}
              />
            </div>

            <div className="flex items-center justify-between p-3 rounded-lg bg-base-300/50">
              <div className="flex items-center gap-3">
                <Info size={18} className="text-base-content/60" />
                <div>
                  <div className="font-medium text-sm">Show Welcome Message</div>
                  <div className="text-xs text-base-content/60">Display welcome tips on the dashboard</div>
                </div>
              </div>
              <input
                type="checkbox"
                className="toggle toggle-primary toggle-sm"
                checked={localSettings.showWelcome}
                onChange={(e) => updateSetting('showWelcome', e.target.checked)}
              />
            </div>
          </div>
        </div>
      </ExpandableSection>

      {/* Project Settings */}
      <ExpandableSection
        title="Project Identity"
        description="Basic project information from project.yaml"
        icon={<Folder size={20} />}
        tooltip={{
          title: 'Project Settings',
          content: 'Project configuration stored in project.yaml. Changes are saved to the project file and affect all users.',
        }}
        isLoading={apiLoading}
      >
        {apiError ? (
          <div className="alert alert-error">
            <AlertCircle size={20} />
            <span>Failed to load project settings</span>
          </div>
        ) : apiSettings?.project ? (
          <SettingsSection
            title=""
            description=""
            icon={null}
            onSave={handleProjectSave}
            onReset={() => setProjectChanges({})}
            hasChanges={Object.keys(projectChanges).length > 0}
            isSaving={updateMutation.isPending}
            compact
          >
            {Object.entries(apiSettings.project).map(([key, setting]) => (
              <SettingField
                key={key}
                name={key}
                setting={{ ...setting, value: key in projectChanges ? projectChanges[key] : setting.value }}
                onChange={(value) => setProjectChanges((prev) => ({ ...prev, [key]: value }))}
              />
            ))}
          </SettingsSection>
        ) : (
          <p className="text-base-content/60">No project settings available</p>
        )}
      </ExpandableSection>

      {/* Project Paths */}
      {apiSettings?.paths && (
        <ExpandableSection
          title="Project Paths"
          description="Directory configuration for content and deliverables"
          icon={<Folder size={20} />}
          tooltip={{
            title: 'Project Paths',
            content: 'Directory paths configured in project.yaml. Content and assets paths are read-only. You can enable desktop deliverables to publish outputs directly to your Desktop folder.',
          }}
        >
          <div className="space-y-4">
            {/* Read-only paths */}
            <div className="space-y-2">
              {Object.entries(apiSettings.paths)
                .filter(([key]) => !['desktop_deliverables', 'publish'].includes(key))
                .map(([key, setting]) => (
                <div key={key} className="flex items-center justify-between p-2 rounded bg-base-300/30">
                  <span className="text-sm font-medium capitalize">{key.replace(/_/g, ' ')}</span>
                  <code className="text-sm text-base-content/60 bg-base-300 px-2 py-0.5 rounded">
                    {String(setting.value) || '-'}
                  </code>
                </div>
              ))}
            </div>

            {/* Desktop Deliverables Toggle */}
            {apiSettings.paths.desktop_deliverables && (
              <div className="border-t border-base-300 pt-4">
                <div className="flex items-center justify-between p-3 rounded-lg bg-base-300/50">
                  <div className="flex items-center gap-3">
                    <Folder size={18} className="text-base-content/60" />
                    <div>
                      <div className="font-medium text-sm">Desktop Deliverables</div>
                      <div className="text-xs text-base-content/60">
                        {apiSettings.paths.desktop_deliverables.description}
                      </div>
                    </div>
                  </div>
                  <input
                    type="checkbox"
                    className="toggle toggle-primary toggle-sm"
                    checked={
                      'desktop_deliverables' in pathsChanges
                        ? Boolean(pathsChanges.desktop_deliverables)
                        : Boolean(apiSettings.paths.desktop_deliverables.value)
                    }
                    onChange={(e) => setPathsChanges((prev) => ({
                      ...prev,
                      desktop_deliverables: e.target.checked,
                    }))}
                  />
                </div>

                {/* Show current publish path */}
                {apiSettings.paths.publish && (
                  <div className="mt-2 flex items-center justify-between p-2 rounded bg-base-300/30">
                    <span className="text-sm font-medium">Publish Path</span>
                    <code className="text-sm text-base-content/60 bg-base-300 px-2 py-0.5 rounded max-w-[300px] truncate">
                      {String(apiSettings.paths.publish.value)}
                    </code>
                  </div>
                )}

                {/* Save/Reset buttons */}
                {Object.keys(pathsChanges).length > 0 && (
                  <div className="flex justify-end gap-2 mt-4">
                    <button
                      className="btn btn-ghost btn-sm"
                      onClick={() => setPathsChanges({})}
                    >
                      Reset
                    </button>
                    <button
                      className="btn btn-primary btn-sm"
                      onClick={handlePathsSave}
                      disabled={updateMutation.isPending}
                    >
                      {updateMutation.isPending ? (
                        <Spinner size="sm" />
                      ) : (
                        'Save'
                      )}
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        </ExpandableSection>
      )}

      {/* Quality Settings */}
      <ExpandableSection
        title="Quality & Readability"
        description="Content quality and readability thresholds"
        icon={<Clock size={20} />}
        tooltip={{
          title: 'Quality Settings',
          content: 'Configure target reading levels for content validation. Documents are checked against these thresholds during quality analysis.',
        }}
        isLoading={apiLoading}
      >
        {apiSettings?.quality ? (
          <SettingsSection
            title=""
            description=""
            icon={null}
            onSave={handleQualitySave}
            onReset={() => setQualityChanges({})}
            hasChanges={Object.keys(qualityChanges).length > 0}
            isSaving={updateMutation.isPending}
            compact
          >
            {Object.entries(apiSettings.quality).map(([key, setting]) => (
              <SettingField
                key={key}
                name={key}
                setting={{ ...setting, value: key in qualityChanges ? qualityChanges[key] : setting.value }}
                onChange={(value) => setQualityChanges((prev) => ({ ...prev, [key]: value }))}
                options={
                  key === 'target_reading_level' ? readingLevelOptions :
                  key === 'target_lix_level' ? lixLevelOptions : undefined
                }
              />
            ))}
          </SettingsSection>
        ) : (
          <p className="text-base-content/60">No quality settings available</p>
        )}
      </ExpandableSection>

      {/* Video Production Settings */}
      {apiSettings?.video && (
        <ExpandableSection
          title="Video Production"
          description="Resolution and encoding settings"
          icon={<Video size={20} />}
          tooltip={{
            title: 'Video Settings',
            content: 'Configure video output parameters including resolution, frame rate, and encoding options for generated videos.',
          }}
        >
          <SettingsSection
            title=""
            description=""
            icon={null}
            onSave={handleVideoSave}
            onReset={() => setVideoChanges({})}
            hasChanges={Object.keys(videoChanges).length > 0}
            isSaving={updateMutation.isPending}
            compact
          >
            {Object.entries(apiSettings.video).map(([key, setting]) => (
              <SettingField
                key={key}
                name={key}
                setting={{ ...setting, value: key in videoChanges ? videoChanges[key] : setting.value }}
                onChange={(value) => setVideoChanges((prev) => ({ ...prev, [key]: value }))}
                options={key === 'fps' ? fpsOptions : undefined}
              />
            ))}
          </SettingsSection>
        </ExpandableSection>
      )}

      {/* Voiceover Settings */}
      {apiSettings?.voiceover && (
        <ExpandableSection
          title="Voiceover"
          description="Text-to-speech configuration"
          icon={<Mic size={20} />}
          tooltip={{
            title: 'Voiceover Settings',
            content: 'Configure text-to-speech provider and voice settings for generating audio narration.',
          }}
        >
          <SettingsSection
            title=""
            description=""
            icon={null}
            onSave={handleVoiceoverSave}
            onReset={() => setVoiceoverChanges({})}
            hasChanges={Object.keys(voiceoverChanges).length > 0}
            isSaving={updateMutation.isPending}
            compact
          >
            {Object.entries(apiSettings.voiceover).map(([key, setting]) => (
              <SettingField
                key={key}
                name={key}
                setting={{ ...setting, value: key in voiceoverChanges ? voiceoverChanges[key] : setting.value }}
                onChange={(value) => setVoiceoverChanges((prev) => ({ ...prev, [key]: value }))}
                options={key === 'provider' ? providerOptions : undefined}
              />
            ))}
          </SettingsSection>
        </ExpandableSection>
      )}

      {/* Environment Variables (read-only) */}
      <ExpandableSection
        title="Environment Variables"
        description="API keys and system configuration (read-only)"
        icon={<Terminal size={20} />}
        tooltip={{
          title: 'Environment Variables',
          content: 'System environment variables detected by Media Engine. These are set outside the application and cannot be modified here.',
        }}
        isLoading={apiLoading}
      >
        {Object.keys(envGroups).length > 0 ? (
          <div className="space-y-6">
            {Object.entries(envGroups).map(([category, vars]) => (
              <div key={category}>
                <h4 className="text-sm font-medium text-base-content/70 mb-3">{category}</h4>
                <div className="space-y-2">
                  {Object.entries(vars).map(([key, setting]) => (
                    <div
                      key={key}
                      className="flex items-center justify-between p-2 rounded bg-base-300/30"
                    >
                      <div className="flex items-center gap-2">
                        <code className="text-sm bg-base-300 px-2 py-0.5 rounded">{key}</code>
                        {setting.sensitive && (
                          <span title="Sensitive">
                            <Shield size={12} className="text-warning" />
                          </span>
                        )}
                      </div>
                      {setting.is_set ? (
                        <span className="badge badge-success badge-sm gap-1">
                          <CheckCircle size={12} />
                          Set
                        </span>
                      ) : (
                        <span className="badge badge-ghost badge-sm gap-1">
                          <AlertCircle size={12} />
                          Not Set
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-base-content/60">No environment variables detected</p>
        )}
      </ExpandableSection>

      {/* System Defaults (read-only) */}
      <ExpandableSection
        title="System Defaults"
        description="Immutable default values"
        icon={<Shield size={20} />}
        tooltip={{
          title: 'System Defaults',
          content: 'Default values built into Media Engine. These cannot be changed and serve as fallbacks when settings are not configured.',
        }}
        isLoading={defaultsLoading}
      >
        {defaults ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Object.entries(defaults).map(([category, categorySettings]) => (
              <div key={category} className="p-3 rounded-lg bg-base-300/50">
                <h4 className="text-sm font-medium capitalize mb-2">{category}</h4>
                <div className="space-y-1 text-xs">
                  {Object.entries(categorySettings as Record<string, SettingValue>)
                    .slice(0, 5)
                    .map(([key, setting]) => (
                      <div key={key} className="flex justify-between">
                        <span className="text-base-content/60">{key}</span>
                        <span className="font-mono">{String(setting.value)}</span>
                      </div>
                    ))}
                  {Object.keys(categorySettings as object).length > 5 && (
                    <div className="text-base-content/40">
                      +{Object.keys(categorySettings as object).length - 5} more
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-base-content/60">No system defaults available</p>
        )}
      </ExpandableSection>

      {/* About */}
      <ExpandableSection
        title="About"
        description="Dashboard information"
        icon={<Settings2 size={20} />}
      >
        <div className="space-y-2">
          <div className="flex justify-between p-2 rounded bg-base-300/30">
            <span className="text-sm text-base-content/60">Dashboard Version</span>
            <span className="font-mono text-sm">1.0.0</span>
          </div>
          <div className="flex justify-between p-2 rounded bg-base-300/30">
            <span className="text-sm text-base-content/60">Settings Sources</span>
            <span className="font-mono text-sm">localStorage + project.yaml + env</span>
          </div>
        </div>
      </ExpandableSection>
    </div>
  );
}
