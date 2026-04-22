import { useRef, useEffect } from 'react';
import { useChatStore } from '@/store/chatStore';
import { usePersonaStore } from '@/store/personaStore';
import { ChatMessage } from '@/ui/reusables/ChatMessage/ChatMessage';
import { ChatInput } from '@/ui/reusables/ChatInput/ChatInput';
import { WelcomeScreen } from '@/ui/reusables/WelcomeScreen/WelcomeScreen';
import { PersonaSetup } from '@/ui/reusables/PersonaSetup/PersonaSetup';
import { PersonaLoader } from '@/ui/reusables/PersonaLoader/PersonaLoader';

export function ChatInterface() {
  const messages = useChatStore((s) => s.messages);
  const isStreaming = useChatStore((s) => s.isStreaming);
  const scrollRef = useRef<HTMLDivElement>(null);

  const appPhase = usePersonaStore((s) => s.appPhase);

  // Auto-scroll on new messages
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isStreaming]);

  // Setup screen (before chat is unlocked)
  if (appPhase === 'setup') {
    return (
      <div className="flex h-full flex-col bg-slate-950">
        <div className="flex-1 overflow-y-auto">
          <PersonaSetup />
        </div>
      </div>
    );
  }

  if (appPhase === 'processing') {
    return (
      <div className="flex h-full flex-col bg-slate-950">
        <div className="flex-1 overflow-y-auto">
          <PersonaLoader />
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col bg-slate-950">
      {/* Messages area */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto">
        {messages.length === 0 ? (
          <WelcomeScreen />
        ) : (
          <div className="mx-auto max-w-3xl px-4 py-4 space-y-4">
            {messages.map((msg) => (
              <ChatMessage key={msg.id} message={msg} />
            ))}
            {isStreaming && (
              <div className="flex items-center gap-2 px-4 py-2">
                <div className="flex gap-1">
                  <div className="h-1.5 w-1.5 rounded-full bg-[#2BB5D4] animate-bounce" style={{ animationDelay: '0ms' }} />
                  <div className="h-1.5 w-1.5 rounded-full bg-[#2BB5D4] animate-bounce" style={{ animationDelay: '150ms' }} />
                  <div className="h-1.5 w-1.5 rounded-full bg-[#2BB5D4] animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Input area */}
      <div className="px-4 pb-4 pt-2">
        <div className="mx-auto max-w-3xl">
          <ChatInput />
        </div>
      </div>
    </div>
  );
}
