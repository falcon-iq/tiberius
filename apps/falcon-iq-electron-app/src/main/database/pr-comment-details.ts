import { getDatabase } from './init';
import { getEarliestOpenGoalTimestamp } from './goals';
import { getLogger } from '@libs/shared/utils/logger';

const log = getLogger({ name: 'pr-comment-details' });

// Types
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

// Constants
const SEVERITY_SCALE = ['TRIVIAL', 'LOW', 'MEDIUM', 'HIGH', 'BLOCKER'];

// Database queries
export function getPRCommentsForUser(username: string, sinceTimestamp?: string | null) {
  try {
    const db = getDatabase();
    let query = 'SELECT * FROM pr_comment_details WHERE is_reviewer = 1 AND username = ?';
    const params: (string | null)[] = [username];

    if (sinceTimestamp) {
      query += ' AND created_at >= ?';
      params.push(sinceTimestamp);
    }

    const stmt = db.prepare(query);
    const comments = stmt.all(...params) as PRCommentRow[];
    return { success: true, data: comments };
  } catch {
    return { success: false, error: 'Failed to fetch PR comments' };
  }
}

// Statistics calculation
export function calculatePRCommentStats(comments: PRCommentRow[]): PRCommentStats {
  const total = comments.length;

  // Distinct counts
  const prCount = new Set(comments.map(c => c.pr_number)).size;
  const authorCount = new Set(comments.map(c => c.pr_author).filter(Boolean)).size;

  // Handle empty case
  if (total === 0) {
    return {
      summary: {
        total_comments: 0,
        pr_count: 0,
        author_count: 0,
      },
      metrics: {
        bugs_in_logic: 0,
        design_thinking: 0,
        balanced_feedback: 0,
        system_level_concerns: {
          total: 0,
          edge_cases: 0,
          reliability: 0,
          performance: 0,
          bug_correctness: 0,
        },
        high_engagement: 0,
        nitpick_rate: 0,
      },
      categories: [],
      severities: SEVERITY_SCALE.map(sev => ({ severity: sev, count: 0, percentage: 0 })),
      rates: { nitpick_rate: 0, actionable_rate: 0, total_comments: 0 }
    };
  }

  // Helper for percentage calculation
  const toPercent = (count: number) => parseFloat(((count / total) * 100).toFixed(1));

  // Calculate metrics
  const bugsInLogic = comments.filter(c =>
    c.primary_category === 'BUG_CORRECTNESS' ||
    c.primary_category === 'PRODUCT_BEHAVIOR'
  ).length;

  const designThinking = comments.filter(c =>
    c.primary_category === 'DESIGN_ARCHITECTURE'
  ).length;

  const balancedFeedback = comments.filter(c =>
    c.primary_category === 'PRAISE_ACK'
  ).length;

  // System-Level sub-metrics
  const edgeCases = comments.filter(c =>
    c.primary_category === 'EDGE_CASES'
  ).length;

  const reliability = comments.filter(c =>
    c.primary_category === 'RELIABILITY_RESILIENCE' || c.mentions_reliability === 1
  ).length;

  const performance = comments.filter(c =>
    c.primary_category === 'PERFORMANCE' || c.mentions_performance === 1
  ).length;

  const bugCorrectness = bugsInLogic; // Same as top-level metric

  const highEngagement = comments.filter(c =>
    c.primary_category === 'QUESTION_CLARIFICATION'
  ).length;

  const nitpicks = comments.filter(c => c.is_nitpick === 1).length;

  // Build new structure
  const metrics: KeyReviewMetrics = {
    bugs_in_logic: toPercent(bugsInLogic),
    design_thinking: toPercent(designThinking),
    balanced_feedback: toPercent(balancedFeedback),
    system_level_concerns: {
      edge_cases: toPercent(edgeCases),
      reliability: toPercent(reliability),
      performance: toPercent(performance),
      bug_correctness: toPercent(bugCorrectness),
      total: toPercent(edgeCases + reliability + performance + bugCorrectness),
    },
    high_engagement: toPercent(highEngagement),
    nitpick_rate: toPercent(nitpicks),
  };

  const summary: PRCommentSummary = {
    total_comments: total,
    pr_count: prCount,
    author_count: authorCount,
  };

  // Legacy calculations for backwards compatibility
  const categoryMap = new Map<string, number>();
  comments.forEach(c => {
    if (c.primary_category) {
      categoryMap.set(c.primary_category, (categoryMap.get(c.primary_category) || 0) + 1);
    }
  });

  const categories: CategoryStat[] = Array.from(categoryMap.entries())
    .map(([category, count]) => ({
      category,
      count,
      percentage: toPercent(count)
    }))
    .sort((a, b) => b.count - a.count);

  const severityMap = new Map<string, number>();
  comments.forEach(c => {
    if (c.severity) {
      severityMap.set(c.severity, (severityMap.get(c.severity) || 0) + 1);
    }
  });

  const severities: SeverityStat[] = SEVERITY_SCALE.map(severity => {
    const count = severityMap.get(severity) || 0;
    return {
      severity,
      count,
      percentage: toPercent(count)
    };
  });

  const actionableCount = comments.filter(c => c.actionability === 'ACTIONABLE').length;

  return {
    summary,
    metrics,
    // Legacy fields
    categories,
    severities,
    rates: {
      nitpick_rate: toPercent(nitpicks),
      actionable_rate: toPercent(actionableCount),
      total_comments: total
    }
  };
}

// Get PR comments filtered by metric type
export function getPRCommentsByMetric(
  username: string,
  metricType: 'bugs_in_logic' | 'design_thinking' | 'balanced_feedback' |
              'edge_cases' | 'reliability' | 'performance' | 'bug_correctness' |
              'high_engagement' | 'nitpick_rate'
) {
  try {
    const timestampResult = getEarliestOpenGoalTimestamp();
    if (!timestampResult.success) {
      return timestampResult;
    }

    const commentsResult = getPRCommentsForUser(username, timestampResult.data);
    if (!commentsResult.success) {
      return commentsResult;
    }

    const allComments = commentsResult.data || [];

    // Filter based on metric type
    let filtered: PRCommentRow[] = [];
    switch (metricType) {
      case 'bugs_in_logic':
      case 'bug_correctness':
        filtered = allComments.filter(c =>
          c.primary_category === 'BUG_CORRECTNESS' ||
          c.primary_category === 'PRODUCT_BEHAVIOR'
        );
        break;
      case 'design_thinking':
        filtered = allComments.filter(c => c.primary_category === 'DESIGN_ARCHITECTURE');
        break;
      case 'balanced_feedback':
        filtered = allComments.filter(c => c.primary_category === 'PRAISE_ACK');
        break;
      case 'edge_cases':
        filtered = allComments.filter(c => c.primary_category === 'EDGE_CASES');
        break;
      case 'reliability':
        filtered = allComments.filter(c =>
          c.primary_category === 'RELIABILITY_RESILIENCE' || c.mentions_reliability === 1
        );
        break;
      case 'performance':
        filtered = allComments.filter(c =>
          c.primary_category === 'PERFORMANCE' || c.mentions_performance === 1
        );
        break;
      case 'high_engagement':
        filtered = allComments.filter(c => c.primary_category === 'QUESTION_CLARIFICATION');
        break;
      case 'nitpick_rate':
        filtered = allComments.filter(c => c.is_nitpick === 1);
        break;
    }

    return { success: true, data: filtered };
  } catch (error) {
    log.error({ error }, 'Error fetching comments by metric');
    return { success: false, error: 'Failed to fetch comments' };
  }
}

// Main function that combines queries and calculation
export function getPRCommentStats(username: string) {
  try {
    // Get earliest open goal timestamp
    const timestampResult = getEarliestOpenGoalTimestamp();
    if (!timestampResult.success) {
      return timestampResult;
    }

    // Get filtered PR comments
    const commentsResult = getPRCommentsForUser(username, timestampResult.data);
    if (!commentsResult.success) {
      return commentsResult;
    }

    // Calculate stats
    const stats = calculatePRCommentStats(commentsResult.data || []);
    return { success: true, data: stats };
  } catch (error) {
    log.error({ error }, 'Error calculating PR comment stats');
    return { success: false, error: 'Failed to calculate PR comment stats' };
  }
}
