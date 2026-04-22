import { MessageSquare, Clock } from 'lucide-react';
import { useChatStore } from '@/store/chatStore';
import { toast } from 'sonner';

export function ConversationHistory() {
  const savedConversations = useChatStore((s) => s.savedConversations);

  const formatTimeAgo = (timestamp: string) => {
    const diff = Date.now() - new Date(timestamp).getTime();
    const minutes = Math.floor(diff / 60000);
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    return `${days}d ago`;
  };

  const handleClick = (title: string) => {
    toast('Conversation history is view-only in this demo', {
      description: `"${title}" — Full restore coming soon`,
    });
  };

  if (savedConversations.length === 0) return null;

  return (
    <div className="border-t border-slate-800 pt-3 mt-2">
      <div className="flex items-center gap-1.5 px-3 mb-2">
        <Clock className="h-3 w-3 text-slate-600" />
        <span className="text-[10px] font-medium text-slate-600 uppercase tracking-wider">
          Recent Conversations
        </span>
      </div>
      <div className="space-y-0.5 px-1">
        {savedConversations.map((conv) => (
          <button
            key={conv.id}
            onClick={() => handleClick(conv.title)}
            className="flex w-full items-start gap-2.5 rounded-md px-2 py-2 text-left hover:bg-slate-800/50 transition-colors group"
          >
            <MessageSquare className="h-3.5 w-3.5 text-slate-600 mt-0.5 flex-shrink-0 group-hover:text-slate-400" />
            <div className="min-w-0 flex-1">
              <p className="text-[11px] font-medium text-slate-400 truncate group-hover:text-slate-200 transition-colors">
                {conv.title}
              </p>
              <div className="flex items-center gap-2 mt-0.5">
                <span className="text-[9px] text-slate-600">
                  {conv.messageCount} messages
                </span>
                <span className="text-[9px] text-slate-700">&middot;</span>
                <span className="text-[9px] text-slate-600">
                  {formatTimeAgo(conv.timestamp)}
                </span>
              </div>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
