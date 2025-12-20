import { useEffect, useRef, useState, useCallback } from 'react';

export type WebSocketMessageType =
  | 'user_joined'
  | 'user_left'
  | 'cursor_update'
  | 'edit'
  | 'document_updated'
  | 'ai_task_update'
  | 'build_status'
  | 'refresh';

export interface WebSocketMessage {
  type: WebSocketMessageType;
  user_id?: string;
  timestamp?: string;
  file?: string;
  line?: number;
  col?: number;
  changes?: unknown;
  data?: unknown;
}

export interface WebSocketState {
  isConnected: boolean;
  users: string[];
  cursors: Record<string, { file: string; line: number; col: number }>;
  lastMessage: WebSocketMessage | null;
}

interface UseWebSocketOptions {
  userId?: string;
  onMessage?: (message: WebSocketMessage) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  autoReconnect?: boolean;
  reconnectInterval?: number;
}

export function useWebSocket(options: UseWebSocketOptions = {}) {
  const {
    userId = `user-${Math.random().toString(36).slice(2, 8)}`,
    onMessage,
    onConnect,
    onDisconnect,
    autoReconnect = true,
    reconnectInterval = 3000,
  } = options;

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [state, setState] = useState<WebSocketState>({
    isConnected: false,
    users: [],
    cursors: {},
    lastMessage: null,
  });

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const wsUrl = `${protocol}//${host}/api/ws/${userId}`;

    try {
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        setState(prev => ({ ...prev, isConnected: true }));
        onConnect?.();
      };

      ws.onclose = () => {
        setState(prev => ({ ...prev, isConnected: false }));
        onDisconnect?.();
        wsRef.current = null;

        if (autoReconnect) {
          reconnectTimeoutRef.current = setTimeout(connect, reconnectInterval);
        }
      };

      ws.onerror = () => {
        ws.close();
      };

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);

          setState(prev => {
            const newState = { ...prev, lastMessage: message };

            switch (message.type) {
              case 'user_joined':
                if (message.user_id && !prev.users.includes(message.user_id)) {
                  newState.users = [...prev.users, message.user_id];
                }
                break;

              case 'user_left':
                if (message.user_id) {
                  newState.users = prev.users.filter(u => u !== message.user_id);
                  const { [message.user_id]: _, ...remainingCursors } = prev.cursors;
                  newState.cursors = remainingCursors;
                }
                break;

              case 'cursor_update':
                if (message.user_id && message.file !== undefined) {
                  newState.cursors = {
                    ...prev.cursors,
                    [message.user_id]: {
                      file: message.file,
                      line: message.line ?? 0,
                      col: message.col ?? 0,
                    },
                  };
                }
                break;
            }

            return newState;
          });

          onMessage?.(message);
        } catch {
          // Invalid JSON, ignore
        }
      };

      wsRef.current = ws;
    } catch {
      if (autoReconnect) {
        reconnectTimeoutRef.current = setTimeout(connect, reconnectInterval);
      }
    }
  }, [userId, onConnect, onDisconnect, onMessage, autoReconnect, reconnectInterval]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  }, []);

  const send = useCallback((message: Partial<WebSocketMessage>) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    }
  }, []);

  const sendCursorUpdate = useCallback((file: string, line: number, col: number) => {
    send({ type: 'cursor_update', file, line, col });
  }, [send]);

  const sendEdit = useCallback((file: string, changes: unknown) => {
    send({ type: 'edit', file, changes });
  }, [send]);

  // Auto-connect on mount
  useEffect(() => {
    connect();
    return () => disconnect();
  }, [connect, disconnect]);

  return {
    ...state,
    userId,
    connect,
    disconnect,
    send,
    sendCursorUpdate,
    sendEdit,
  };
}
