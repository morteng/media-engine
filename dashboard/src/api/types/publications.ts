/**
 * Publication-related type definitions
 */

export interface PublicationOutput {
  format: string;
  template: string;
  filename: string;
  single_file: boolean;
  toc: boolean;
}

export interface PublicationChapter {
  path: string;
  required: boolean;
  sections: string[];
}

export interface PublicationMetadata {
  version: string;
  status: string;
  author: string;
  copyright: string;
  license: string;
  isbn: string | null;
  edition: string;
  publication_date: string | null;
  target_audience: string;
  reading_time: string;
}

export interface PublicationValidation {
  is_valid: boolean;
  issues: string[];
  chapter_count: number;
  missing_chapters: number;
  translation_current: boolean;
  source_changed: boolean;
}

export interface Publication {
  key: string;
  title: string;
  subtitle: string;
  language: string;
  status: string;
  version: string;
  chapter_count: number;
  output_formats: string[];
  is_translation: boolean;
  source_document: string | null;
}

export interface PublicationDetail extends Publication {
  pub_type?: string;
  description: string;
  metadata: PublicationMetadata;
  chapters: PublicationChapter[];
  outputs: PublicationOutput[];
  source_hash: string | null;
  validation: PublicationValidation;
  assets: string[];
  related: string[];
}

export interface PublicationsResponse {
  publications: Publication[];
  total: number;
}

export interface PublicationStatusItem {
  key: string;
  title: string;
  language: string;
  pub_type: 'book' | 'deck' | 'spreadsheet' | 'report';
  status: string;
  is_valid: boolean;
  issues_count: number;
  item_count: number;
  item_label: 'chapters' | 'slides' | 'sources';
  chapter_count: number;
  slide_count: number;
  data_source_count: number;
  missing_chapters: number;
  is_translation: boolean;
  translation_current: boolean;
  source_changed: boolean;
}

export interface PublicationsStatusResponse {
  publications: PublicationStatusItem[];
  summary: {
    total: number;
    valid: number;
    invalid: number;
    translations_current: number;
    translations_outdated: number;
    total_issues: number;
  };
}

export interface PublicationTranslationPair {
  source: {
    key: string;
    title: string;
    language: string;
    content_hash: string;
  };
  translation: {
    key: string;
    title: string;
    language: string;
    source_hash: string | null;
  };
  sync_status: {
    is_current: boolean;
    source_changed: boolean;
    needs_update: boolean;
  };
}

export interface PublicationTranslationsResponse {
  pairs: PublicationTranslationPair[];
  total: number;
  outdated: number;
}
