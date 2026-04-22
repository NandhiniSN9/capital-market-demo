import { cn } from '@/helpers/utilities/utils';

interface ConfidenceIndicatorProps {
  level: 'high' | 'medium' | 'low';
  reason: string;
}

const levelConfig = {
  high: {
    label: 'High Confidence',
    color: 'text-emerald-400',
    dotColor: 'bg-emerald-400',
    bgColor: 'bg-emerald-500/5',
    borderColor: 'border-emerald-500/10',
    dots: 3,
  },
  medium: {
    label: 'Medium Confidence',
    color: 'text-amber-400',
    dotColor: 'bg-amber-400',
    bgColor: 'bg-amber-500/5',
    borderColor: 'border-amber-500/10',
    dots: 2,
  },
  low: {
    label: 'Low Confidence',
    color: 'text-red-400',
    dotColor: 'bg-red-400',
    bgColor: 'bg-red-500/5',
    borderColor: 'border-red-500/10',
    dots: 1,
  },
};

export function ConfidenceIndicator({ level, reason }: ConfidenceIndicatorProps) {
  const config = levelConfig[level];

  return (
    <div className={cn('flex items-center gap-2 rounded-md border px-2.5 py-1.5', config.bgColor, config.borderColor)}>
      <div className="flex gap-0.5">
        {[1, 2, 3].map((i) => (
          <div
            key={i}
            className={cn(
              'h-1.5 w-1.5 rounded-full',
              i <= config.dots ? config.dotColor : 'bg-slate-700'
            )}
          />
        ))}
      </div>
      <span className={cn('text-[10px] font-medium', config.color)}>{config.label}</span>
      <span className="text-[10px] text-slate-500">&middot;</span>
      <span className="text-[10px] text-slate-500 truncate">{reason}</span>
    </div>
  );
}
