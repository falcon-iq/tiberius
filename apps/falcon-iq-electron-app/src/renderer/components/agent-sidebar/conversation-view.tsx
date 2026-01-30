import { useEffect, useRef } from 'react';
import { MessageBubble } from './message-bubble';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: number;
  status: 'pending' | 'success' | 'error';
  error?: string;
}

interface ConversationViewProps {
  messages: Message[];
  isLoading?: boolean;
  onRetry?: (messageId: string) => void;
}

function LoadingSkeleton() {
  return (
    <div className="flex flex-col gap-4 p-4 animate-pulse">
      <div className="flex flex-col items-end">
        <div className="bg-muted rounded-2xl h-12 w-3/4 ml-auto" />
      </div>
      <div className="flex flex-col items-start">
        <div className="bg-muted rounded-2xl h-20 w-4/5 mr-auto" />
      </div>
      <div className="flex flex-col items-end">
        <div className="bg-muted rounded-2xl h-10 w-2/3 ml-auto" />
      </div>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="flex items-center justify-center h-full p-8">
      <div className="text-center space-y-2">
        <p className="text-muted-foreground">
          Ask your Agent anything about your PRs, OKRs, or code reviews
        </p>
      </div>
    </div>
  );
}

export function ConversationView({ messages, isLoading, onRetry }: ConversationViewProps) {
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const prevMessageCountRef = useRef(messages.length);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (messages.length > prevMessageCountRef.current) {
      const container = scrollContainerRef.current;
      if (container) {
        // Smooth scroll to bottom
        container.scrollTo({
          top: container.scrollHeight,
          behavior: 'smooth',
        });
      }
    }
    prevMessageCountRef.current = messages.length;
  }, [messages.length]);

  if (isLoading) {
    return <LoadingSkeleton />;
  }

  if (messages.length === 0) {
    return <EmptyState />;
  }

  return (
    <div
      ref={scrollContainerRef}
      className="flex-1 overflow-y-auto p-4 space-y-2"
    >
      {messages.map((message) => (
        <MessageBubble
          key={message.id}
          role={message.role}
          content={message.content}
          timestamp={message.timestamp}
          status={message.status}
          error={message.error}
          onRetry={
            message.status === 'error' && onRetry
              ? () => onRetry(message.id)
              : undefined
          }
        />
      ))}
    </div>
  );
}
