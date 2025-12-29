/**
 * Build-related type definitions
 */

export interface BuildLogEntry {
  timestamp: string;
  message: string;
  level: 'info' | 'success' | 'warning' | 'error';
}

export interface BuildOutput {
  path: string;
  name: string;
  format: string;
  language: string;
  size: number;
  modified: string;
}

export interface FreshnessWarning {
  stale: number;
  expired: number;
  message: string;
}

export interface BuildStatus {
  active: boolean;
  progress: number;
  logs: BuildLogEntry[];
  last_build: string | null;
  freshness_warning: FreshnessWarning | null;
  outputs: BuildOutput[];
  // Legacy fields for backward compatibility
  isBuilding?: boolean;
  lastBuild?: string;
  lastBuildStatus?: 'success' | 'failed';
  availableFormats?: string[];
}

export interface BuildStartResponse {
  status: 'started' | 'error';
  formats: string[];
  languages: string[];
  force: boolean;
  message?: string;
}

export interface BuildOutputsResponse {
  outputs: BuildOutput[];
}

export interface DeliverableConfig {
  output_dir: string;
  package_name: string;
  include_source: boolean;
  create_zip: boolean;
  version_folders: boolean;
}

export interface AuditLogEntry {
  timestamp: string;
  action: string;
  details?: string;
  user?: string;
}

// Unified build types
export interface UnifiedBuildPublication {
  key: string;
  formats: string[];
  languages: string[];
}

export interface UnifiedBuildRequest {
  publications: UnifiedBuildPublication[];
  outputDir?: string;
  includeFonts?: boolean;
  includeDiagrams?: boolean;
  includeVideos?: boolean;
  includeNavigation?: boolean;
  publish?: boolean;
  preset?: string;
}

export interface PublicationBuildInfo {
  key: string;
  title: string;
  pub_type: string;
  formats: string[];
  languages: string[];
  isStale?: boolean;
}

export interface BuildPublicationsResponse {
  publications: PublicationBuildInfo[];
}

export interface BuildPreset {
  name: string;
  description?: string;
  formats: string[];
  languages: string[];
}

export interface BuildPresetsResponse {
  presets: BuildPreset[];
}

export interface PublishConfiguration {
  defaultDir: string;
  desktopDir: string;
  useDesktop: boolean;
}
