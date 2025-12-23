import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react';

// Theme type - just nord (light) and sunset (dark)
export type Theme = 'nord' | 'sunset';

// Settings interface
export interface Settings {
  theme: Theme;
  compactMode: boolean;
  showWelcome: boolean;
}

// Default settings
const defaultSettings: Settings = {
  theme: 'sunset',
  compactMode: false,
  showWelcome: true,
};

// localStorage key
const STORAGE_KEY = 'media-engine-settings';

// Context interface
interface SettingsContextType {
  settings: Settings;
  updateSetting: <K extends keyof Settings>(key: K, value: Settings[K]) => void;
  setTheme: (theme: Theme) => void;
  toggleTheme: () => void;
  resetSettings: () => void;
  isDark: boolean;
}

// Create context
const SettingsContext = createContext<SettingsContextType | null>(null);

// Load settings from localStorage
function loadSettings(): Settings {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      const parsed = JSON.parse(stored);
      // Merge with defaults to handle new settings
      return { ...defaultSettings, ...parsed };
    }
  } catch (error) {
    console.error('Failed to load settings:', error);
  }
  return defaultSettings;
}

// Save settings to localStorage
function saveSettings(settings: Settings): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
  } catch (error) {
    console.error('Failed to save settings:', error);
  }
}

// Provider component
export function SettingsProvider({ children }: { children: ReactNode }) {
  const [settings, setSettings] = useState<Settings>(loadSettings);

  // Apply theme to document on mount and when theme changes
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', settings.theme);
    saveSettings(settings);
  }, [settings]);

  // Update a single setting
  const updateSetting = useCallback(<K extends keyof Settings>(key: K, value: Settings[K]) => {
    setSettings(prev => ({ ...prev, [key]: value }));
  }, []);

  // Set theme specifically
  const setTheme = useCallback((theme: Theme) => {
    setSettings(prev => ({ ...prev, theme }));
  }, []);

  // Toggle between nord and sunset
  const toggleTheme = useCallback(() => {
    setSettings(prev => ({
      ...prev,
      theme: prev.theme === 'nord' ? 'sunset' : 'nord'
    }));
  }, []);

  // Reset to defaults
  const resetSettings = useCallback(() => {
    setSettings(defaultSettings);
  }, []);

  // Convenience boolean for dark mode
  const isDark = settings.theme === 'sunset';

  return (
    <SettingsContext.Provider value={{
      settings,
      updateSetting,
      setTheme,
      toggleTheme,
      resetSettings,
      isDark
    }}>
      {children}
    </SettingsContext.Provider>
  );
}

// Hook to use settings
export function useSettings(): SettingsContextType {
  const context = useContext(SettingsContext);
  if (!context) {
    throw new Error('useSettings must be used within a SettingsProvider');
  }
  return context;
}
