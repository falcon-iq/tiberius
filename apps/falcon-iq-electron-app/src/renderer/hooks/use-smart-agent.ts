import { useMutation, useQuery } from '@tanstack/react-query';
import { useCallback, useEffect, useState } from 'react';
import type { CapabilitiesResponse, QueryResponse } from '../types/electron';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: number;
  status: 'pending' | 'success' | 'error';
  error?: string;
}

const CONVERSATION_HISTORY_KEY = 'agent-conversation-history';

/**
 * Hook to fetch agent capabilities with 5-minute cache
 */
export function useAgentCapabilities() {
  return useQuery({
    queryKey: ['agent-capabilities'],
    queryFn: async () => {
      const response = await window.api.smartAgent.getCapabilities();
      if (!response.success) {
        throw new Error(response.error || 'Failed to fetch capabilities');
      }
      return response.data as CapabilitiesResponse;
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 2,
  });
}

/**
 * Hook to send queries to the smart agent
 */
export function useAgentQuery() {
  return useMutation({
    mutationFn: async (query: string) => {
      const response = await window.api.smartAgent.query(query);
      if (!response.success) {
        throw new Error(response.error || 'Failed to query agent');
      }
      return response.data as QueryResponse;
    },
  });
}

/**
 * Hook to manage conversation history with localStorage persistence
 */
export function useConversationHistory() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Load conversation history from localStorage on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem(CONVERSATION_HISTORY_KEY);
      if (stored) {
        const parsed = JSON.parse(stored) as Message[];
        setMessages(parsed);
      }
    } catch (error) {
      console.error('Failed to load conversation history:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Save to localStorage whenever messages change
  useEffect(() => {
    if (!isLoading) {
      try {
        localStorage.setItem(CONVERSATION_HISTORY_KEY, JSON.stringify(messages));
      } catch (error) {
        console.error('Failed to save conversation history:', error);
      }
    }
  }, [messages, isLoading]);

  const addMessage = useCallback((message: Omit<Message, 'id' | 'timestamp'>) => {
    const newMessage: Message = {
      ...message,
      id: `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`,
      timestamp: Date.now(),
    };
    setMessages((prev) => [...prev, newMessage]);
    return newMessage.id;
  }, []);

  const updateMessage = useCallback((id: string, updates: Partial<Message>) => {
    setMessages((prev) =>
      prev.map((msg) => (msg.id === id ? { ...msg, ...updates } : msg))
    );
  }, []);

  const clearHistory = useCallback(() => {
    setMessages([]);
    try {
      localStorage.removeItem(CONVERSATION_HISTORY_KEY);
    } catch (error) {
      console.error('Failed to clear conversation history:', error);
    }
  }, []);

  return {
    messages,
    isLoading,
    addMessage,
    updateMessage,
    clearHistory,
  };
}
