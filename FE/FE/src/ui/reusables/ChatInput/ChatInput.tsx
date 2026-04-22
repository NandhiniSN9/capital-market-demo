import { useState, useRef, useEffect } from 'react';
import { ArrowUp, Loader2 } from 'lucide-react';
import { useChatStore } from '@/store/chatStore';

export function ChatInput() {
  const [input, setInput] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const isStreaming = useChatStore((s) => s.isStreaming);

  useEffect(() => {
    textareaRef.current?.focus();
  }, []);

  useEffect(() => {
    const el = textareaRef.current;
    if (el) {
      el.style.height = 'auto';
      el.style.height = Math.min(el.scrollHeight, 120) + 'px';
    }
  }, [input]);

  // ChatInput in the legacy AppShell is not wired to the real send flow.
  // The active ChatPanel in ChatScreen.tsx handles sending directly.
  const handleSend = () => { setInput(''); };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); }
  };

  return (
    <div className="relative flex items-center gap-2 rounded-2xl border border-slate-700/80 bg-slate-900/60 px-4 py-3 focus-within:border-[#145D70]/50 focus-within:ring-1 focus-within:ring-[#145D70]/20 transition-all">
      <textarea
        ref={textareaRef}
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Ask a question about the documents..."
        disabled={isStreaming}
        rows={1}
        className="flex-1 resize-none bg-transparent text-sm leading-6 text-slate-200 placeholder-slate-500 outline-none disabled:opacity-50"
      />
      <button
        onClick={handleSend}
        disabled={!input.trim() || isStreaming}
        className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg bg-[#145D70] text-white hover:bg-[#1A7A92] disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
      >
        {isStreaming
          ? <Loader2 className="h-4 w-4 animate-spin stroke-[1.5]" />
          : <ArrowUp className="h-4 w-4 stroke-[2]" />}
      </button>
    </div>
  );
}
