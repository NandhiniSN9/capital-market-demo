import { Loader2, CheckCircle2, FileText } from 'lucide-react';
import { useProcessingVM } from './ProcessingScreen.vm.ts';
import { TopBar } from '../../reusables/TopBar/TopBar.tsx';
import './ProcessingScreen.css';

export function ProcessingScreen() {
  const { companyName, steps, statuses, progress, doneCount } = useProcessingVM();

  return (
    <div className="processing-root">
      <TopBar />
      <main className="processing-body">
        <div className="processing-inner">
          <header className="processing-header">
            <div className="processing-icon-wrap" aria-hidden="true">
              <Loader2 size={28} style={{ color: '#2BB5D4' }} className="animate-spin" strokeWidth={1.5} />
            </div>
            <h1 className="processing-title">Processing {companyName}</h1>
            <p className="processing-subtitle">Reading company filings and disclosures...</p>
          </header>

          <div
            aria-live="polite"
            aria-label={`Processing ${doneCount} of ${steps.length} sources`}
            className="sr-only"
          >
            {doneCount} of {steps.length} sources processed
          </div>

          <ol className="processing-steps" aria-label="Processing steps">
            {steps.map((step, i) => {
              const status = statuses[i];
              return (
                <li
                  key={i}
                  className={`processing-step processing-step--${status}`}
                  aria-label={`${step.label}: ${status}`}
                >
                  <div className={`processing-step-icon processing-step-icon--${status}`} aria-hidden="true">
                    {status === 'done' ? (
                      <CheckCircle2 size={16} style={{ color: '#4ade80' }} strokeWidth={1.5} />
                    ) : status === 'active' ? (
                      <Loader2 size={16} style={{ color: '#2BB5D4' }} className="animate-spin" strokeWidth={1.5} />
                    ) : (
                      <FileText size={16} style={{ color: '#475569' }} strokeWidth={1.5} />
                    )}
                  </div>
                  <span className={`processing-step-label processing-step-label--${status}`}>
                    {status === 'active' ? 'Reading ' : status === 'done' ? 'Read ' : ''}
                    <strong>{step.label}</strong>
                  </span>
                </li>
              );
            })}
          </ol>

          <div className="processing-progress-wrap" role="progressbar" aria-valuenow={Math.round(progress)} aria-valuemin={0} aria-valuemax={100} aria-label="Overall processing progress">
            <div className="processing-progress-bar-bg">
              <div className="processing-progress-bar" style={{ width: `${progress}%` }} />
            </div>
            <p className="processing-progress-text">
              {doneCount} of {steps.length} sources processed
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}
