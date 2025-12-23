import { useSettings, type Theme } from '@/contexts';
import { Card, CardContent } from '@/components/ui';
import { Moon, Sun, RotateCcw, Monitor } from 'lucide-react';

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

export function Settings() {
  const { settings, setTheme, updateSetting, resetSettings } = useSettings();

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Settings</h1>
          <p className="text-base-content/60 mt-1">Customize your dashboard experience</p>
        </div>
        <button
          className="btn btn-ghost btn-sm gap-2"
          onClick={resetSettings}
        >
          <RotateCcw size={16} />
          Reset to Defaults
        </button>
      </div>

      {/* Appearance Section */}
      <Card>
        <div className="p-4 border-b border-base-300">
          <h2 className="text-lg font-semibold flex items-center gap-2">
            <Monitor size={20} />
            Appearance
          </h2>
          <p className="text-sm text-base-content/60 mt-1">
            Choose your preferred theme
          </p>
        </div>
        <CardContent className="p-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {themes.map((theme) => {
              const Icon = theme.icon;
              const isSelected = settings.theme === theme.id;
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
                  {isSelected && (
                    <div className="badge badge-primary badge-sm">Active</div>
                  )}
                </button>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Dashboard Section */}
      <Card>
        <div className="p-4 border-b border-base-300">
          <h2 className="text-lg font-semibold">Dashboard</h2>
          <p className="text-sm text-base-content/60 mt-1">
            Configure dashboard behavior
          </p>
        </div>
        <CardContent className="p-4 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="font-medium">Compact Mode</div>
              <div className="text-sm text-base-content/60">Use smaller spacing and fonts</div>
            </div>
            <input
              type="checkbox"
              className="toggle toggle-primary"
              checked={settings.compactMode}
              onChange={(e) => updateSetting('compactMode', e.target.checked)}
            />
          </div>

          <div className="divider my-0"></div>

          <div className="flex items-center justify-between">
            <div>
              <div className="font-medium">Show Welcome Message</div>
              <div className="text-sm text-base-content/60">Display welcome tips on the dashboard</div>
            </div>
            <input
              type="checkbox"
              className="toggle toggle-primary"
              checked={settings.showWelcome}
              onChange={(e) => updateSetting('showWelcome', e.target.checked)}
            />
          </div>
        </CardContent>
      </Card>

      {/* About Section */}
      <Card>
        <div className="p-4 border-b border-base-300">
          <h2 className="text-lg font-semibold">About</h2>
        </div>
        <CardContent className="p-4">
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-base-content/60">Dashboard Version</span>
              <span className="font-mono">1.0.0</span>
            </div>
            <div className="flex justify-between">
              <span className="text-base-content/60">Settings Storage</span>
              <span className="font-mono">localStorage</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
