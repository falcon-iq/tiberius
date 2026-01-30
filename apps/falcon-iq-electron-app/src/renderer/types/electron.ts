export interface User {
  id: number;
  username: string;
  github_suffix: string | null;
  email_address: string | null;
  firstname: string | null;
  lastname: string | null;
}

export interface AddUserInput {
  username: string;
  github_suffix?: string | null;
  email_address?: string | null;
  firstname?: string | null;
  lastname?: string | null;
}

export interface Goal {
  id: number;
  goal: string;
  start_date: string;
  end_date: string | null;
}

export interface AddGoalInput {
  goal: string;
  start_date?: string | null;
  end_date?: string | null;
}

export interface UpdateGoalInput {
  id: number;
  end_date?: string | null;
}

export interface KeyReviewMetrics {
  bugs_in_logic: number;
  design_thinking: number;
  balanced_feedback: number;
  system_level_concerns: {
    total: number;
    edge_cases: number;
    reliability: number;
    performance: number;
    bug_correctness: number;
  };
  high_engagement: number;
  nitpick_rate: number;
}

export interface PRCommentSummary {
  total_comments: number;
  pr_count: number;
  author_count: number;
}

export interface CategoryStat {
  category: string;
  count: number;
  percentage: number;
}

export interface SeverityStat {
  severity: string;
  count: number;
  percentage: number;
}

export interface PRCommentStats {
  summary: PRCommentSummary;
  metrics: KeyReviewMetrics;
  // Legacy fields for backwards compatibility
  categories?: CategoryStat[];
  severities?: SeverityStat[];
  rates?: {
    nitpick_rate: number;
    actionable_rate: number;
    total_comments: number;
  };
}

export interface DatabaseResult<T> {
  success: boolean;
  data?: T;
  error?: string;
}

export interface AppSettings {
  version: string;
  user: {
    firstName: string;
    lastName: string;
    ldapUsername: string;
  };
  integrations: {
    github: {
      pat: string;
      emuSuffix?: string;
      username?: string;
    };
  };
  onboardingCompleted: boolean;
}

export interface SettingsResult<T> {
  success: boolean;
  data?: T;
  error?: string;
}

// Python server response types
export interface PRDetails {
  owner: string;
  repo: string;
  pr_number: number;
  pr_title: string;
  pr_body: string;
  pr_author: string;
  pr_created_at: string;
  pr_html_url: string;
}

export interface CommentDetails {
  pr_number: number;
  comment_id: number;
  user: string;
  body: string;
  created_at: string;
  is_reviewer: boolean;
  path: string;
  line: number | null;
}

export interface PRCommentRow {
  pr_number: number;
  comment_id: number;
  username: string;
  comment_type: string | null;
  created_at: string | null;
  is_reviewer: number | null;
  line: number | null;
  side: string | null;
  pr_author: string | null;
  primary_category: string | null;
  secondary_categories: string | null;
  severity: string | null;
  confidence: number | null;
  actionability: string | null;
  rationale: string | null;
  is_ai_reviewer: number | null;
  is_nitpick: number | null;
  mentions_tests: number | null;
  mentions_bug: number | null;
  mentions_design: number | null;
  mentions_performance: number | null;
  mentions_reliability: number | null;
  mentions_security: number | null;
}

export type MetricType =
  | 'bugs_in_logic'
  | 'design_thinking'
  | 'balanced_feedback'
  | 'edge_cases'
  | 'reliability'
  | 'performance'
  | 'bug_correctness'
  | 'high_engagement'
  | 'nitpick_rate';

// Python server types imported from shared location
import type {
  PythonServerStatus,
  PythonServerState,
  PythonServerResult,
} from '../../shared/types/python-server';

// Re-export for external consumers
export type {
  PythonServerStatus,
  PythonServerState,
  PythonServerResult,
};

export interface ElectronAPI {
  getUsers(): Promise<DatabaseResult<User[]>>;
  addUser(user: AddUserInput): Promise<DatabaseResult<User>>;
  deleteUser(id: number): Promise<DatabaseResult<void>>;
  getGoals(): Promise<DatabaseResult<Goal[]>>;
  addGoal(goal: AddGoalInput): Promise<DatabaseResult<Goal>>;
  deleteGoal(id: number): Promise<DatabaseResult<void>>;
  updateGoal(goal: UpdateGoalInput): Promise<DatabaseResult<void>>;
  getPRCommentStats(username: string): Promise<DatabaseResult<PRCommentStats>>;
  getPRCommentsByMetric(username: string, metricType: MetricType): Promise<DatabaseResult<PRCommentRow[]>>;
  python: {
    getStatus(): Promise<PythonServerStatus>;
    restart(): Promise<PythonServerResult<PythonServerState>>;
    getPR(prId: number): Promise<DatabaseResult<PRDetails>>;
    getComment(prId: number, commentId: number): Promise<DatabaseResult<CommentDetails>>;
    getPRFiles(prId: number): Promise<DatabaseResult<any>>;
  };
  pythonServer: {
    getStatus(): Promise<PythonServerStatus>;
    restart(): Promise<PythonServerResult<PythonServerState>>;
  };
  settings: {
    get(): Promise<SettingsResult<AppSettings>>;
    save(settings: AppSettings): Promise<SettingsResult<void>>;
    update(partial: Partial<AppSettings>): Promise<SettingsResult<void>>;
  };
}

declare global {
  interface Window {
    api: ElectronAPI;
  }
}
