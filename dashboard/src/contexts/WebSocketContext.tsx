import { createContext, useContext, useCallback, type ReactNode } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useWebSocket, type WebSocketMessage, type WebSocketState } from '@/hooks/useWebSocket';

interface WebSocketContextValue extends WebSocketState {
  userId: string;
  connect: () => void;
  disconnect: () => void;
  send: (message: Partial<WebSocketMessage>) => void;
  sendCursorUpdate: (file: string, line: number, col: number) => void;
  sendEdit: (file: string, changes: unknown) => void;
}

const WebSocketContext = createContext<WebSocketContextValue | null>(null);

interface WebSocketProviderProps {
  children: ReactNode;
}

export function WebSocketProvider({ children }: WebSocketProviderProps) {
  const queryClient = useQueryClient();

  const handleMessage = useCallback((message: WebSocketMessage) => {
    // Invalidate relevant queries based on message type
    switch (message.type) {
      case 'document_updated':
        // Invalidate document queries when a document is updated
        queryClient.invalidateQueries({ queryKey: ['documents'] });
        queryClient.invalidateQueries({ queryKey: ['document'] });
        queryClient.invalidateQueries({ queryKey: ['file'] });
        break;

      case 'ai_task_update':
        // Invalidate AI task queries
        queryClient.invalidateQueries({ queryKey: ['aiTasks'] });
        queryClient.invalidateQueries({ queryKey: ['aiQueueStats'] });
        break;

      case 'build_status':
        // Invalidate build-related queries
        queryClient.invalidateQueries({ queryKey: ['build'] });
        break;

      // Video production events
      case 'render_started':
      case 'render_progress':
      case 'render_complete':
      case 'render_failed':
      case 'render_cancelled':
        // Invalidate render queue queries
        queryClient.invalidateQueries({ queryKey: ['renderQueue'] });
        break;

      case 'script_updated':
        // Invalidate video script queries
        queryClient.invalidateQueries({ queryKey: ['videoScripts'] });
        queryClient.invalidateQueries({ queryKey: ['videoScript'] });
        break;

      case 'refresh':
        // Invalidate all queries for a full refresh
        queryClient.invalidateQueries();
        break;

      case 'file_change': {
        // File system change detected - invalidate based on refresh hints
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const refresh = (message as any).refresh as string[] | undefined;
        if (refresh?.includes('all')) {
          queryClient.invalidateQueries();
        } else {
          if (refresh?.includes('documents')) {
            queryClient.invalidateQueries({ queryKey: ['documents'] });
            queryClient.invalidateQueries({ queryKey: ['document'] });
          }
          if (refresh?.includes('translations')) {
            queryClient.invalidateQueries({ queryKey: ['translations'] });
          }
          if (refresh?.includes('quality')) {
            queryClient.invalidateQueries({ queryKey: ['quality'] });
            queryClient.invalidateQueries({ queryKey: ['health'] });
          }
          if (refresh?.includes('project')) {
            queryClient.invalidateQueries({ queryKey: ['project'] });
            queryClient.invalidateQueries({ queryKey: ['status'] });
          }
          if (refresh?.includes('brand')) {
            queryClient.invalidateQueries({ queryKey: ['brand'] });
          }
          if (refresh?.includes('freshness')) {
            queryClient.invalidateQueries({ queryKey: ['freshness'] });
          }
          if (refresh?.includes('media')) {
            queryClient.invalidateQueries({ queryKey: ['media'] });
          }
          if (refresh?.includes('video')) {
            queryClient.invalidateQueries({ queryKey: ['videoScripts'] });
            queryClient.invalidateQueries({ queryKey: ['videoAssets'] });
            queryClient.invalidateQueries({ queryKey: ['renderQueue'] });
          }
        }
        break;
      }

      case 'edit':
        // Could show a toast notification about remote edits
        break;
    }
  }, [queryClient]);

  const ws = useWebSocket({
    onMessage: handleMessage,
  });

  return (
    <WebSocketContext.Provider value={ws}>
      {children}
    </WebSocketContext.Provider>
  );
}

export function useWebSocketContext() {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useWebSocketContext must be used within a WebSocketProvider');
  }
  return context;
}

// Optional hook that doesn't throw if not in provider
export function useOptionalWebSocket() {
  return useContext(WebSocketContext);
}
