import { Wifi, WifiOff, Users } from 'lucide-react';
import { useOptionalWebSocket } from '@/contexts';
import './ConnectionStatus.css';

export function ConnectionStatus() {
  const ws = useOptionalWebSocket();

  if (!ws) {
    return null;
  }

  const { isConnected, users } = ws;
  const userCount = users.length;

  return (
    <div className={`connection-status ${isConnected ? 'connected' : 'disconnected'}`}>
      <div className="connection-indicator" title={isConnected ? 'Connected' : 'Disconnected'}>
        {isConnected ? <Wifi size={14} /> : <WifiOff size={14} />}
      </div>
      {isConnected && userCount > 0 && (
        <div className="user-count" title={`${userCount} other user${userCount !== 1 ? 's' : ''} online`}>
          <Users size={12} />
          <span>{userCount}</span>
        </div>
      )}
    </div>
  );
}
