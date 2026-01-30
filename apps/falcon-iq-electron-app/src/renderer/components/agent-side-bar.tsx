import { Sparkles, ChevronLeft, ChevronRight, Trash2 } from 'lucide-react';
import { useState } from 'react';
import {
  useAgentCapabilities,
  useAgentQuery,
  useConversationHistory,
} from '../hooks/use-smart-agent';
import { CapabilitiesPanel } from './agent-sidebar/capabilities-panel';
import { ChatInput } from './agent-sidebar/chat-input';
import { ConversationView } from './agent-sidebar/conversation-view';

interface AgentSidebarProps {
  isCollapsed: boolean;
  width: number;
  collapsedWidth: number;
  isResizing: boolean;
  onToggleCollapse: () => void;
  onWidthChange: (width: number) => void;
  onResizeStart: () => void;
  onResizeEnd: () => void;
}

const AgentSidebar = ({
  isCollapsed,
  width,
  collapsedWidth,
  isResizing,
  onToggleCollapse,
  onWidthChange,
  onResizeStart,
  onResizeEnd,
}: AgentSidebarProps) => {
  const [inputValue, setInputValue] = useState('');

  // Hooks for agent capabilities and conversation
  const { data: capabilitiesData, isLoading: isLoadingCapabilities } = useAgentCapabilities();
  const { mutate: sendQuery, isPending } = useAgentQuery();
  const { messages, isLoading: isLoadingHistory, addMessage, updateMessage, clearHistory } =
    useConversationHistory();

  const handleMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    onResizeStart();

    const startX = e.clientX;
    const startWidth = width;

    const handleMouseMove = (moveEvent: MouseEvent) => {
      const deltaX = moveEvent.clientX - startX;
      const newWidth = startWidth - deltaX; // Right sidebar, so subtract
      onWidthChange(newWidth);
    };

    const handleMouseUp = () => {
      onResizeEnd();
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
  };

  const handleSend = () => {
    if (!inputValue.trim() || isPending) return;

    const query = inputValue.trim();
    setInputValue('');

    // Add user message
    addMessage({
      role: 'user',
      content: query,
      status: 'success',
    });

    // Add pending assistant message
    const assistantMessageId = addMessage({
      role: 'assistant',
      content: '',
      status: 'pending',
    });

    // Send query to agent
    sendQuery(query, {
      onSuccess: (response) => {
        updateMessage(assistantMessageId, {
          content: response.answer,
          status: 'success',
        });
      },
      onError: (error) => {
        updateMessage(assistantMessageId, {
          content: '',
          status: 'error',
          error: error.message || 'Failed to get response from Agent',
        });
      },
    });
  };

  const handleSelectExample = (example: string) => {
    setInputValue(example);
  };

  const handleRetry = (messageId: string) => {
    const message = messages.find((msg) => msg.id === messageId);
    if (!message) return;

    // Find the user message before this assistant message
    const messageIndex = messages.findIndex((msg) => msg.id === messageId);
    const userMessage = messages
      .slice(0, messageIndex)
      .reverse()
      .find((msg) => msg.role === 'user');

    if (!userMessage) return;

    // Update assistant message to pending
    updateMessage(messageId, {
      status: 'pending',
      error: undefined,
    });

    // Retry query
    sendQuery(userMessage.content, {
      onSuccess: (response) => {
        updateMessage(messageId, {
          content: response.answer,
          status: 'success',
        });
      },
      onError: (error) => {
        updateMessage(messageId, {
          status: 'error',
          error: error.message || 'Failed to get response from Agent',
        });
      },
    });
  };

  const handleClearHistory = () => {
    if (confirm('Are you sure you want to clear the conversation history?')) {
      clearHistory();
    }
  };

  return (
    <aside
      className={`relative flex flex-col border-l border-sidebar-border bg-sidebar ${
        !isResizing ? 'transition-[width] duration-300 ease-in-out' : ''
      }`}
      style={{ width: isCollapsed ? `${collapsedWidth}px` : `${width}px` }}
    >
      {/* Drag Handle */}
      {!isCollapsed && (
        <div
          className="absolute left-0 top-0 h-full cursor-col-resize border-r border-sidebar-border hover:bg-primary/10 active:bg-primary/20"
          style={{ width: '4px', marginLeft: '-2px' }}
          onMouseDown={handleMouseDown}
        />
      )}

      {/* Header with toggle */}
      <div className="flex h-16 items-center gap-2 border-b border-sidebar-border px-4">
        <button
          onClick={onToggleCollapse}
          className="flex h-8 w-8 items-center justify-center rounded-lg hover:bg-muted"
          aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {isCollapsed ? (
            <ChevronLeft className="h-4 w-4" />
          ) : (
            <ChevronRight className="h-4 w-4" />
          )}
        </button>
        {!isCollapsed && (
          <>
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10">
              <Sparkles className="h-4 w-4 text-primary" />
            </div>
            <div className="flex-1">
              <h2 className="text-sm font-semibold text-foreground">Agent</h2>
              <p className="text-xs text-muted-foreground">Your helpful assistant</p>
            </div>
            {messages.length > 0 && (
              <button
                onClick={handleClearHistory}
                className="flex h-8 w-8 items-center justify-center rounded-lg hover:bg-muted text-muted-foreground hover:text-destructive transition-colors"
                aria-label="Clear conversation history"
              >
                <Trash2 className="h-4 w-4" />
              </button>
            )}
          </>
        )}
      </div>

      {!isCollapsed && (
        <>
          {/* Conversation View */}
          <ConversationView
            messages={messages}
            isLoading={isLoadingHistory}
            onRetry={handleRetry}
          />

          {/* Capabilities Panel */}
          {!isLoadingCapabilities && capabilitiesData?.capabilities && (
            <CapabilitiesPanel
              capabilities={capabilitiesData.capabilities}
              onSelectExample={handleSelectExample}
              collapsed={messages.length > 0}
            />
          )}

          {/* Chat Input */}
          <ChatInput
            value={inputValue}
            onChange={setInputValue}
            onSend={handleSend}
            disabled={isPending}
            isLoading={isPending}
          />
        </>
      )}
    </aside>
  );
};

export default AgentSidebar;
