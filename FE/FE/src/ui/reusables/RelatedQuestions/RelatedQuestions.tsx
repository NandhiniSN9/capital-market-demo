import { Sparkles } from 'lucide-react';

interface RelatedQuestionsProps {
  questions: string[];
  onSendQuestion?: (q: string) => void;
}

export function RelatedQuestions({ questions, onSendQuestion }: RelatedQuestionsProps) {
  return (
    <div>
      <div className="flex items-center gap-1.5 mb-2">
        <Sparkles className="h-3 w-3 text-sky-400" />
        <span className="text-[10px] font-medium text-slate-500">Related questions</span>
      </div>
      <div className="flex flex-wrap gap-1.5">
        {questions.slice(0, 4).map((q, i) => (
          <button
            key={i}
            onClick={() => onSendQuestion?.(q)}
            className="rounded-lg border border-slate-800 bg-slate-900/50 px-3 py-1.5 text-[11px] text-slate-400 hover:border-sky-500/30 hover:text-sky-300 hover:bg-slate-800/50 transition-all"
          >
            {q}
          </button>
        ))}
      </div>
    </div>
  );
}
