import { DocumentLibrary } from '../DocumentLibrary/DocumentLibrary';
import { ConversationHistory } from '../ConversationHistory/ConversationHistory';

export function LeftPanel() {
  return (
    <div className="flex h-full flex-col bg-slate-950 border-r border-slate-800/50">
      {/* Document section: takes up to 60% of the panel, scrolls internally */}
      <div className="flex flex-col min-h-0 max-h-[60%] shrink overflow-hidden">
        <DocumentLibrary />
      </div>
      {/* Conversation history: always visible at the bottom */}
      <div className="flex-1 min-h-0 overflow-y-auto">
        <ConversationHistory />
      </div>
    </div>
  );
}
