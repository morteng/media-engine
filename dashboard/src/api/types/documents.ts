/**
 * Document-related type definitions
 */

export interface PublicationRef {
  key: string;
  title: string;
  pub_type: 'book' | 'deck' | 'spreadsheet' | 'report';
  item_count: number;
  item_label: 'chapters' | 'slides' | 'sources';
}

export interface Document {
  path: string;
  filename: string;
  title: string;
  type: 'chapter' | 'deliverable' | 'script' | 'slides' | 'diagram' | 'data' | 'demo';
  language: string;
  frontmatter?: Record<string, unknown>;
  publication?: PublicationRef | null;
}

export interface DocumentContent {
  path: string;
  filename: string;
  title: string;
  content: string;
  html?: string;
  metadata?: Record<string, unknown>;
}

export interface Translation {
  source: string;
  target: string;
  sourceLanguage: string;
  targetLanguage: string;
  status: 'synced' | 'outdated' | 'missing';
  sourceVersion?: string;
  targetVersion?: string;
}

export interface TranslationMatrix {
  documents: string[];
  languages: string[];
  matrix: Record<string, Record<string, Translation | null>>;
}
