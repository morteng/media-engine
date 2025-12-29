/**
 * AI Workspace type definitions
 */

export interface AISession {
  id: string;
  task_id: string;
  status: 'active' | 'paused' | 'completed' | 'failed';
  started_at: string;
  last_active?: string;
  completed_at?: string;
  progress: {
    total_steps: number;
    completed_steps: number;
    current_step?: string;
  };
  changes: Array<{
    type: string;
    path: string;
    description: string;
    timestamp: string;
  }>;
}

export interface AISessionsResponse {
  sessions: AISession[];
  active_count: number;
  total_count: number;
}

export type NoteType =
  | 'uncertainty'
  | 'suggestion'
  | 'human_review'
  | 'decision'
  | 'todo'
  | 'warning'
  | 'info';

export interface AINote {
  id: string;
  type: NoteType;
  content: string;
  context?: string;
  document_path?: string;
  created_at: string;
  resolved: boolean;
  resolved_at?: string;
  resolution?: string;
}

export interface AINotesResponse {
  notes: AINote[];
  unresolved_count: number;
  total_count: number;
}

export interface AITask {
  id: string;
  type: string;
  description: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  status: 'pending' | 'claimed' | 'in_progress' | 'completed' | 'failed';
  created_at: string;
  claimed_by?: string;
  claimed_at?: string;
  completed_at?: string;
  document_path?: string;
  context?: Record<string, unknown>;
}

export interface AITaskQueueResponse {
  tasks: AITask[];
  pending_count: number;
  in_progress_count: number;
}

export interface AIResearchEntry {
  key: string;
  value: unknown;
  context?: string;
  tags: string[];
  created_at: string;
  updated_at: string;
  is_stale: boolean;
  confidence?: number;
}

export interface AIResearchResponse {
  entries: AIResearchEntry[];
  stale_count: number;
  total_count: number;
}

export interface AIDecision {
  id: string;
  decision: string;
  rationale: string;
  context: string;
  document_path?: string;
  session_id?: string;
  created_at: string;
}

export interface AIDecisionsResponse {
  decisions: AIDecision[];
  total_count: number;
}

export interface AIContextData {
  project: {
    name: string;
    languages: string[];
    document_count: number;
  };
  publications: {
    total: number;
    valid: number;
    stale: number;
  };
  active_session?: {
    id: string;
    task_id: string;
    progress: number;
  };
  pending_tasks: number;
  unresolved_notes: number;
  stale_research: number;
  recent_decisions: number;
  health_score: number;
  last_refresh: string;
}

export interface AIContextResponse {
  context: AIContextData;
  success: boolean;
}
