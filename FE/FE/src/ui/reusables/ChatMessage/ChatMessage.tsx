import { MessageBO as Message } from '@/types/chat/ChatBO.ts';
import { AIResponse } from '@/ui/reusables/AIResponse/AIResponse';
import { cn } from '@/helpers/utilities/utils';
import { useChatStore } from '@/store/chatStore';
import { usePersonaStore } from '@/store/personaStore';
import { getPersonaPhoto } from '@/helpers/data/personaProfiles';

interface ChatMessageProps {
  message: Message;
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isStreaming = useChatStore((s) => s.isStreaming);
  const streamingMessageId = useChatStore((s) => s.streamingMessageId);
  const isCurrentlyStreaming = isStreaming && streamingMessageId === message.id;
  const activePersona = usePersonaStore((s) => s.activePersona);
  const profilePhoto = getPersonaPhoto(activePersona.id);

  if (message.role === 'user') {
    return (
      <div className="flex justify-end">
        <div className="flex items-start gap-2.5 max-w-[85%]">
          <div className="rounded-2xl rounded-tr-sm bg-[#d0dee2] px-4 py-2.5">
            <p className="text-sm text-slate-900 leading-relaxed">{message.content}</p>
          </div>
          <img
            src={profilePhoto}
            alt="You"
            className="h-7 w-7 flex-shrink-0 rounded-full object-cover mt-0.5"
          />
        </div>
      </div>
    );
  }

  return (
    <AIResponse
      message={message}
      isStreaming={isCurrentlyStreaming}
    />
  );
}
