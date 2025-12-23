import { Wifi, WifiOff, Users } from 'lucide-react';
import { useOptionalWebSocket } from '@/contexts';

export function ConnectionStatus() {
  const ws = useOptionalWebSocket();

  if (!ws) {
    return null;
  }

  const { isConnected, users } = ws;
  const userCount = users.length;

  return (
    <div className="flex items-center gap-2">
      <div
        className={`flex items-center justify-center w-8 h-8 rounded-lg transition-colors ${
          isConnected
            ? 'text-success bg-success/10'
            : 'text-error bg-error/10'
        }`}
        title={isConnected ? 'Connected' : 'Disconnected'}
      >
        {isConnected ? <Wifi size={14} /> : <WifiOff size={14} />}
      </div>
      {isConnected && userCount > 0 && (
        <div
          className="flex items-center gap-1 px-2 py-1 rounded-md bg-base-300 text-xs text-base-content/70"
          title={`${userCount} other user${userCount !== 1 ? 's' : ''} online`}
        >
          <Users size={12} />
          <span>{userCount}</span>
        </div>
      )}
    </div>
  );
}
