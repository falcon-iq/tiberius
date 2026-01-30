import { Modal } from '@libs/shared/ui/modal';
import { useState, useEffect } from 'react';
import { Calendar, User, Hash, ChevronDown, ChevronUp } from 'lucide-react';
import type { PRCommentRow, MetricType } from '../types/electron';

interface CommentDetailsModalProps {
  isOpen: boolean;
  onClose: () => void;
  username: string;
  metricType: MetricType;
  metricName: string;
}

interface CommentWithBody extends PRCommentRow {
  body?: string;
  bodyLoading?: boolean;
}

export function CommentDetailsModal({
  isOpen,
  onClose,
  username,
  metricType,
  metricName,
}: CommentDetailsModalProps) {
  const [comments, setComments] = useState<CommentWithBody[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedPR, setExpandedPR] = useState<number | null>(null);

  useEffect(() => {
    if (isOpen) {
      fetchComments();
    }
  }, [isOpen, username, metricType]);

  async function fetchComments() {
    setLoading(true);
    const result = await window.api.getPRCommentsByMetric(username, metricType);
    if (result.success) {
      setComments(result.data || []);
    }
    setLoading(false);
  }

  // Fetch comment body from Python server when PR is expanded
  async function fetchCommentBodies(prNumber: number, prComments: CommentWithBody[]) {
    // Mark comments as loading
    setComments(prev => prev.map(c =>
      c.pr_number === prNumber && c.comment_id === prComments.find(pc => pc.comment_id === c.comment_id)?.comment_id
        ? { ...c, bodyLoading: true }
        : c
    ));

    // Fetch bodies for all comments in this PR
    const bodies = await Promise.all(
      prComments.map(async (comment) => {
        try {
          const result = await window.api.python.getComment(prNumber, comment.comment_id);
          // The response is double-nested: { success, data: { success, data: { body, ... } } }
          if (result.success && result.data && result.data.success && result.data.data) {
            return { commentId: comment.comment_id, body: result.data.data.body };
          }
        } catch (error) {
          console.error(`Failed to fetch comment ${comment.comment_id}:`, error);
        }
        return { commentId: comment.comment_id, body: undefined };
      })
    );

    // Update comments with fetched bodies
    setComments(prev => prev.map(c => {
      const bodyData = bodies.find(b => b.commentId === c.comment_id);
      if (bodyData) {
        return { ...c, body: bodyData.body, bodyLoading: false };
      }
      return c;
    }));
  }

  function handlePRToggle(prNumber: number, prComments: CommentWithBody[]) {
    const isExpanding = expandedPR !== prNumber;
    setExpandedPR(isExpanding ? prNumber : null);

    // Fetch comment bodies when expanding (only if not already fetched)
    if (isExpanding && prComments.some(c => !c.body && !c.bodyLoading)) {
      fetchCommentBodies(prNumber, prComments);
    }
  }

  // Group comments by PR
  const commentsByPR = comments.reduce((acc, comment) => {
    if (!acc[comment.pr_number]) {
      acc[comment.pr_number] = [];
    }
    acc[comment.pr_number].push(comment);
    return acc;
  }, {} as Record<number, CommentWithBody[]>);

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={metricName}
      size="xl"
    >
      <div className="space-y-4">
        {/* Summary Stats */}
        <div className="flex gap-4 text-sm text-muted-foreground border-b border-border pb-4">
          <span>{comments.length} comments</span>
          <span>{Object.keys(commentsByPR).length} PRs</span>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="text-center py-8 text-muted-foreground">
            Loading comments...
          </div>
        )}

        {/* Comments Grouped by PR */}
        {!loading && (
          <div className="space-y-3 max-h-[60vh] overflow-y-auto">
            {Object.entries(commentsByPR).map(([prNumber, prComments]) => (
              <div key={prNumber} className="border border-border rounded-lg overflow-hidden">
                {/* PR Header (Clickable to expand) */}
                <button
                  onClick={() => handlePRToggle(Number(prNumber), prComments)}
                  className="w-full flex items-center gap-3 p-4 bg-muted/30 hover:bg-muted/50 transition-colors text-left"
                >
                  <Hash className="w-4 h-4 text-muted-foreground" />
                  <span className="font-semibold">PR #{prNumber}</span>
                  <span className="text-sm text-muted-foreground">
                    {prComments.length} {prComments.length === 1 ? 'comment' : 'comments'}
                  </span>
                  <span className="ml-auto text-xs text-muted-foreground">
                    by {prComments[0].pr_author}
                  </span>
                  {expandedPR === Number(prNumber) ? (
                    <ChevronUp className="w-4 h-4 text-muted-foreground" />
                  ) : (
                    <ChevronDown className="w-4 h-4 text-muted-foreground" />
                  )}
                </button>

                {/* Comments List (Expandable) */}
                {expandedPR === Number(prNumber) && (
                  <div className="divide-y divide-border">
                    {prComments.map((comment) => (
                      <div key={comment.comment_id} className="p-4 bg-card space-y-2">
                        {/* Comment Metadata */}
                        <div className="flex items-center gap-3 text-xs text-muted-foreground flex-wrap">
                          <span className="flex items-center gap-1">
                            <User className="w-3 h-3" />
                            {comment.username}
                          </span>
                          {comment.created_at && (
                            <span className="flex items-center gap-1">
                              <Calendar className="w-3 h-3" />
                              {new Date(comment.created_at).toLocaleDateString()}
                            </span>
                          )}
                          {comment.severity && (
                            <span className="px-2 py-0.5 rounded text-xs font-medium bg-yellow-500/10 text-yellow-500">
                              {comment.severity}
                            </span>
                          )}
                          {comment.is_nitpick === 1 && (
                            <span className="px-2 py-0.5 rounded text-xs font-medium bg-blue-500/10 text-blue-500">
                              Nitpick
                            </span>
                          )}
                        </div>

                        {/* Comment Body (actual comment text) */}
                        {comment.bodyLoading ? (
                          <div className="flex items-center gap-2 text-sm text-muted-foreground">
                            <div className="h-4 w-4 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                            Loading comment...
                          </div>
                        ) : comment.body ? (
                          <div className="space-y-2">
                            <div className="text-sm font-semibold text-foreground">Comment:</div>
                            <p className="text-sm text-foreground bg-muted/30 p-3 rounded border border-border">
                              {comment.body}
                            </p>
                          </div>
                        ) : null}

                        {/* Category */}
                        {comment.primary_category && (
                          <div className="text-xs text-primary font-medium">
                            {comment.primary_category.replace(/_/g, ' ')}
                          </div>
                        )}

                        {/* Rationale (AI explanation) */}
                        {comment.rationale && (
                          <div className="space-y-1">
                            <div className="text-xs font-semibold text-muted-foreground">AI Analysis:</div>
                            <p className="text-xs text-muted-foreground italic">
                              {comment.rationale}
                            </p>
                          </div>
                        )}

                        {/* File Context */}
                        {comment.line !== null && (
                          <div className="text-xs text-muted-foreground font-mono">
                            Line {comment.line} ({comment.side})
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Empty State */}
        {!loading && comments.length === 0 && (
          <div className="text-center py-8 text-muted-foreground">
            No comments found for this metric
          </div>
        )}
      </div>
    </Modal>
  );
}
