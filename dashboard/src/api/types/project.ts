/**
 * Project-related type definitions
 */

export interface Project {
  name: string;
  path: string;
  languages: string[];
  defaultLanguage: string;
  theme?: ThemeConfig;
}

export interface ThemeConfig {
  name: string;
  colors: {
    primary: string;
    secondary: string;
    accent: string;
  };
}

export interface ProjectStatus {
  project: {
    name: string;
    root: string;
  };
  languages: string[];
  source_language: string;
  content: Record<string, Record<string, number>>;
  cache: {
    voiceover_items: number;
    builds_tracked: number;
  };
}

export interface RecentProject {
  path: string;
  name: string;
  last_accessed: string;
  exists: boolean;
}

export interface RecentProjectsResponse {
  current: {
    path: string;
    name: string;
  } | null;
  recent: RecentProject[];
}

export interface OpenProjectResponse {
  status: 'switched' | 'error';
  project?: {
    path: string;
    name: string;
  };
  error?: string;
}

export interface BrowseProjectResponse {
  status: 'selected' | 'prompt' | 'invalid';
  path: string | null;
  message?: string;
  error?: string;
}
