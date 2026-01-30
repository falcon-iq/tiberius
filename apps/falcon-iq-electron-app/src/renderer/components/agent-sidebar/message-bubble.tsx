import { RotateCcw } from 'lucide-react';
import { MarkdownRenderer } from './markdown-renderer';

interface MessageBubbleProps {
  role: 'user' | 'assistant';
  content: string;
  timestamp: number;
  status: 'pending' | 'success' | 'error';
  error?: string;
  onRetry?: () => void;
}

function formatRelativeTime(timestamp: number): string {
  const now = Date.now();
  const diff = now - timestamp;
  const seconds = Math.floor(diff / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);

  if (seconds < 60) return 'just now';
  if (minutes < 60) return `${minutes}m ago`;
  if (hours < 24) return `${hours}h ago`;
  if (days < 7) return `${days}d ago`;
  return new Date(timestamp).toLocaleDateString();
}

export function MessageBubble({
  role,
  content,
  timestamp,
  status,
  error,
  onRetry,
}: MessageBubbleProps) {
  const isUser = role === 'user';
  const isPending = status === 'pending';
  const isError = status === 'error';

  if (isUser) {
    return (
      <div className="flex flex-col items-end mb-4">
        <div className="bg-primary text-primary-foreground rounded-2xl px-4 py-2 ml-auto max-w-[80%]">
          <p className="whitespace-pre-wrap break-words">{content}</p>
        </div>
        <span className="text-xs text-muted-foreground mt-1 mr-2">
          {formatRelativeTime(timestamp)}
        </span>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-start mb-4">
      <div
        className={`bg-card border rounded-2xl px-4 py-3 mr-auto max-w-[85%] ${
          isError ? 'border-destructive' : 'border-border'
        }`}
      >
        {isPending && (
          <div className="flex items-center gap-2">
            <div className="flex gap-1">
              <span className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
              <span className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
              <span className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
            </div>
            <span className="text-sm text-muted-foreground">Thinking...</span>
          </div>
        )}

        {isError && (
          <div className="space-y-2">
            <p className="text-destructive font-medium">Error</p>
            <p className="text-sm">{error || 'An unexpected error occurred'}</p>
            {onRetry && (
              <button
                onClick={onRetry}
                className="flex items-center gap-2 text-sm text-primary hover:underline mt-2"
              >
                <RotateCcw className="w-4 h-4" />
                Retry
              </button>
            )}
          </div>
        )}

        {status === 'success' && (
          <div className="prose prose-sm max-w-none">
            <MarkdownRenderer content={content} />
          </div>
        )}
      </div>
      <span className="text-xs text-muted-foreground mt-1 ml-2">
        {formatRelativeTime(timestamp)}
      </span>
    </div>
  );
}
