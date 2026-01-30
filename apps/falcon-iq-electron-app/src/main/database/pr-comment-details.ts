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
  categories: CategoryStat[];
  severities: SeverityStat[];
  rates: {
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

    console.log("Query --------->", query, params)
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

  // Handle empty case
  if (total === 0) {
    return {
      categories: [],
      severities: SEVERITY_SCALE.map(sev => ({ severity: sev, count: 0, percentage: 0 })),
      rates: { nitpick_rate: 0, actionable_rate: 0, total_comments: 0 }
    };
  }

  // Category distribution
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
      percentage: parseFloat(((count / total) * 100).toFixed(1))
    }))
    .sort((a, b) => b.count - a.count); // Sort by count descending

  // Severity distribution (maintain scale order)
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
      percentage: parseFloat(((count / total) * 100).toFixed(1))
    };
  });

  // Rates
  const nitpickCount = comments.filter(c => c.is_nitpick === 1).length;
  const actionableCount = comments.filter(c => c.actionability === 'ACTIONABLE').length;

  return {
    categories,
    severities,
    rates: {
      nitpick_rate: parseFloat(((nitpickCount / total) * 100).toFixed(1)),
      actionable_rate: parseFloat(((actionableCount / total) * 100).toFixed(1)),
      total_comments: total
    }
  };
}

// Main function that combines queries and calculation
export function getPRCommentStats(username: string) {
  try {
    // Get earliest open goal timestamp
    const timestampResult = getEarliestOpenGoalTimestamp();
    if (!timestampResult.success) {
      return timestampResult;
    }
    console.log("Timestamp ---------->", timestampResult);

    // Get filtered PR comments
    const commentsResult = getPRCommentsForUser(username, timestampResult.data);
    if (!commentsResult.success) {
      return commentsResult;
    }
    console.log("CommentsResult ----------->", commentsResult);

    // Calculate stats
    const stats = calculatePRCommentStats(commentsResult.data || []);
    return { success: true, data: stats };
  } catch (error) {
    log.error({ error }, 'Error calculating PR comment stats');
    return { success: false, error: 'Failed to calculate PR comment stats' };
  }
}
