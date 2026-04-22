import { Plus, FileText, ArrowRight, Calendar, CheckCircle2, Clock, Info } from 'lucide-react';
import { useLandingVM } from './LandingScreen.vm.ts';
import { TopBar } from '../../reusables/TopBar/TopBar.tsx';
import './LandingScreen.css';

export function LandingScreen() {
  const {
    activePersona, chats, loading, error, pollingChatId, isActivelyPolling,
    handleStartNew, handleLoadChat, formatRelativeDate,
  } = useLandingVM();

  const isPolling = isActivelyPolling;

  return (
    <div className="landing-root">
      <TopBar />
      <main className="landing-body">
        <div className="landing-inner">
          <div className="landing-toolbar">
            <div>
              <h1 className="landing-toolbar-title">{activePersona.name}</h1>
              <p className="landing-toolbar-subtitle">Select a past analysis or start a new one</p>
            </div>
            <button
              className="landing-new-btn"
              onClick={handleStartNew}
              disabled={loading || isPolling}
              aria-label={isPolling ? 'Cannot start new analysis while documents are being processed' : 'Start a new analysis'}
              aria-disabled={loading || isPolling}
              title={isPolling ? 'Please wait for the current analysis to finish processing' : undefined}
            >
              <Plus size={16} strokeWidth={1.5} aria-hidden="true" />
              Start New Analysis
            </button>
          </div>

          <section aria-label="Past analyses">
            <span className="sr-only" aria-live="polite" aria-atomic="true">
              {loading ? 'Loading analyses, please wait.' : `${chats.length} analyses loaded.`}
            </span>
            {isPolling && (
              <p className="landing-polling-notice" aria-live="polite" role="status">
                <Clock size={14} strokeWidth={1.5} aria-hidden="true" />
                Processing new analysis — you can still open other chats below.
              </p>
            )}
            <div className="landing-table-wrap" role="region" aria-label="Analysis history">
              <table className="landing-table">
                <thead>
                  <tr>
                    <th scope="col">Company</th>
                    <th scope="col">Sector</th>
                    <th scope="col">Documents</th>
                    <th scope="col">Status</th>
                    <th scope="col">Date Analyzed</th>
                    <th scope="col"><span className="sr-only">Open</span></th>
                  </tr>
                </thead>
                <tbody>
                  {loading ? (
                    Array.from({ length: 5 }).map((_, i) => (
                      <tr key={i} aria-hidden="true">
                        <td><div className="landing-skeleton-cell" style={{ width: '70%' }} /></td>
                        <td><div className="landing-skeleton-cell" style={{ width: '55%' }} /></td>
                        <td><div className="landing-skeleton-cell" style={{ width: '40%' }} /></td>
                        <td><div className="landing-skeleton-cell" style={{ width: '60%' }} /></td>
                        <td><div className="landing-skeleton-cell" style={{ width: '65%' }} /></td>
                        <td />
                      </tr>
                    ))
                  ) : error ? (
                    <tr>
                      <td colSpan={6} className="landing-empty" role="alert">
                        <span style={{ color: '#f87171' }}>{error}</span>
                      </td>
                    </tr>
                  ) : chats.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="landing-empty">
                        No analyses yet. Start your first one!
                      </td>
                    </tr>
                  ) : (
                    chats.map((chat) => {
                      const isThisPolling = chat.chatId === pollingChatId;
                      const isProcessing = chat.status === 'in_progress' || chat.status === 'processing';
                      const isClickDisabled = isProcessing;
                      return (
                        <tr
                          key={chat.chatId}
                          className={`landing-table-row${isThisPolling ? ' landing-table-row--processing' : ''}`}
                          onClick={() => !isClickDisabled && handleLoadChat(chat)}
                          onKeyDown={(e) => {
                            if ((e.key === 'Enter' || e.key === ' ') && !isClickDisabled) {
                              e.preventDefault();
                              handleLoadChat(chat);
                            }
                          }}
                          tabIndex={isClickDisabled ? -1 : 0}
                          role="button"
                          aria-label={
                            isProcessing
                              ? `${chat.companyName} — documents are being processed, navigation disabled`
                              : `Open analysis for ${chat.companyName}`
                          }
                          aria-disabled={isClickDisabled}
                          style={{ cursor: isClickDisabled ? 'not-allowed' : 'pointer', opacity: isClickDisabled ? 0.6 : 1 }}
                        >
                          <td>
                            <div className="landing-td-company-wrap">
                              {isThisPolling && (
                                <span className="landing-new-badge" aria-label="New — processing">
                                  New
                                </span>
                              )}
                              <span className="landing-td-company">{chat.companyName}</span>
                              {isProcessing && (
                                <span className="landing-info-tooltip-wrap" aria-hidden="true">
                                  <Info size={13} className="landing-info-icon" />
                                  <span className="landing-info-tooltip" role="tooltip">
                                    The documents are being processed, please wait for a while in order to navigate to this chat.
                                  </span>
                                </span>
                              )}
                            </div>
                          </td>
                          <td><span className="landing-td-sector">{chat.companySector}</span></td>
                          <td>
                            <span className="landing-td-docs">
                              <FileText size={14} strokeWidth={1.5} aria-hidden="true" />
                              {chat.documentCount}
                            </span>
                          </td>
                          <td>
                            {chat.status === 'active' || chat.status === 'completed' ? (
                              <span className="landing-status-completed">
                                <CheckCircle2 size={14} strokeWidth={1.5} aria-hidden="true" />
                                {chat.status === 'active' ? 'Active' : 'Completed'}
                              </span>
                            ) : chat.status === 'in_progress' ? (
                              <span className="landing-status-progress">
                                <Clock size={14} strokeWidth={1.5} aria-hidden="true" />
                                In Progress
                              </span>
                            ) : chat.status === 'failed' ? (
                              <span className="landing-status-progress">
                                <Clock size={14} strokeWidth={1.5} aria-hidden="true" />
                                Failed
                              </span>
                            ) : (
                              <span className="landing-status-progress">
                                <Clock size={14} strokeWidth={1.5} aria-hidden="true" />
                                {chat.status ?? 'Unknown'}
                              </span>
                            )}
                          </td>
                          <td>
                            <span className="landing-td-date">
                              <Calendar size={14} strokeWidth={1.5} aria-hidden="true" />
                              {formatRelativeDate(chat.updatedAt ?? chat.createdAt ?? '')}
                            </span>
                          </td>
                          <td className="landing-td-action">
                            {!isClickDisabled && (
                              <ArrowRight size={16} strokeWidth={1.5} aria-hidden="true" style={{ color: '#64748b', display: 'inline-block' }} />
                            )}
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          </section>
        </div>
      </main>
    </div>
  );
}
 