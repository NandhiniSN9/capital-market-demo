import { useState, useRef, useId, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import secureStorage from 'react-secure-storage';
import { usePersonaStore } from '../../../store/personaStore.ts';
import { getPersonaConfig } from '../../../helpers/data/personaConfig.ts';
import { chatListService } from '../../../services/chatservice/chatListServiceSelector.ts';
import { ServiceResultStatusENUM } from '../../../types/service/ServiceResultStatusENUM.ts';
import { SECURE_STORAGE_KEYS } from '../../../helpers/storage/secureStorageKeys.ts';
import { PERSONA_TO_ANALYST_TYPE } from '../../../helpers/config/analystTypeMap.ts';
import { setPollingChat } from '../../../helpers/storage/pollingChatMap.ts';

interface CompanySuggestion {
  name: string;
  ticker: string;
  url: string;
}

// Featured companies shown on input focus
const FEATURED_COMPANIES: CompanySuggestion[] = [
  { name: 'Apple Inc.', ticker: 'AAPL', url: 'https://investor.apple.com' },
  { name: 'JPMorgan Chase & Co.', ticker: 'JPM', url: 'https://www.jpmorganchase.com/ir' },
  { name: 'Pfizer Inc.', ticker: 'PFE', url: 'https://www.pfizer.com/investors' },
  { name: 'ExxonMobil Corporation', ticker: 'XOM', url: 'https://corporate.exxonmobil.com/investors' },
  { name: 'Amazon Inc.', ticker: 'AMZN', url: 'https://ir.aboutamazon.com' },
];

const COMPANY_SUGGESTIONS: CompanySuggestion[] = [
  ...FEATURED_COMPANIES,
];

function filterSuggestions(query: string): CompanySuggestion[] {
  if (!query.trim()) return FEATURED_COMPANIES;
  const q = query.toLowerCase();
  return COMPANY_SUGGESTIONS.filter(
    (c) => c.name.toLowerCase().includes(q) || c.ticker.toLowerCase().includes(q)
  ).slice(0, 6);
}

export function useSetupVM() {
  const navigate = useNavigate();
  const activePersona = usePersonaStore((s) => s.activePersona);
  const submitSetup = usePersonaStore((s) => s.submitSetup);
  const setAppPhase = usePersonaStore((s) => s.setAppPhase);

  const config = getPersonaConfig(activePersona.id);

  const [companyName, setCompanyName] = useState('');
  const [companyUrl, setCompanyUrl] = useState('');
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);
  const [suggestions, setSuggestions] = useState<CompanySuggestion[]>([]);
  const [showDropdown, setShowDropdown] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [existingCompanies, setExistingCompanies] = useState<Set<string>>(new Set());

  // Fetch existing chats to know which companies are already taken
  useEffect(() => {
    const analystType = PERSONA_TO_ANALYST_TYPE[activePersona.id];
    chatListService.getChats({ analyst_type: analystType }).then((result) => {
      if (result.statusCode === ServiceResultStatusENUM.OK && result.data) {
        const names = new Set(result.data.chats.map((c) => c.company_name.toLowerCase()));
        setExistingCompanies(names);
      }
    });
  }, [activePersona.id]);

  const inputRef = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const nameId = useId();
  const urlId = useId();
  const fileId = useId();

  const isCompanyTaken = existingCompanies.has(companyName.trim().toLowerCase());
  const canSubmit = companyName.trim().length > 0 && companyUrl.trim().length > 0 && !submitting && !isCompanyTaken;

  const handleNameChange = (value: string) => {
    setCompanyName(value);
    setActiveIndex(-1);
    const results = filterSuggestions(value);
    setSuggestions(results);
    setShowDropdown(results.length > 0);
  };

  const handleInputFocus = () => {
    const results = filterSuggestions(companyName);
    setSuggestions(results);
    setShowDropdown(results.length > 0);
  };

  const selectSuggestion = (s: CompanySuggestion) => {
    if (existingCompanies.has(s.name.toLowerCase())) return; // Don't select taken companies
    setCompanyName(s.name);
    setCompanyUrl(s.url);
    setSuggestions([]);
    setShowDropdown(false);
    setActiveIndex(-1);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!showDropdown) return;
    if (e.key === 'ArrowDown') { e.preventDefault(); setActiveIndex((i) => Math.min(i + 1, suggestions.length - 1)); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); setActiveIndex((i) => Math.max(i - 1, 0)); }
    else if (e.key === 'Enter' && activeIndex >= 0) { e.preventDefault(); selectSuggestion(suggestions[activeIndex]); }
    else if (e.key === 'Escape') { setShowDropdown(false); }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) setUploadedFiles((prev) => [...prev, ...Array.from(e.target.files!)]);
  };

  const removeFile = (index: number) => setUploadedFiles((prev) => prev.filter((_, i) => i !== index));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!canSubmit) return;

    try {
      setSubmitting(true);
      setSubmitError(null);

      const analystType = PERSONA_TO_ANALYST_TYPE[activePersona.id];

      const result = await chatListService.createChat({
        companyName: companyName.trim(),
        companyUrl: companyUrl.trim(),
        analystType,
        files: uploadedFiles.length > 0 ? uploadedFiles : undefined,
      });

      if (result.statusCode === ServiceResultStatusENUM.CREATED && result.data) {
        const chatId = result.data.chat_id;

        secureStorage.setItem(SECURE_STORAGE_KEYS.ACTIVE_CHAT_ID, chatId);
        setPollingChat(analystType, chatId);

        // Update persona store for company context
        submitSetup({ name: companyName.trim(), url: companyUrl.trim() });

        // Navigate to ProcessingScreen for the animation, which will then go to /landing
        navigate('/processing');
      } else {
        setSubmitError(result.message || 'Failed to create analysis. Please try again.');
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'An unexpected error occurred.';
      setSubmitError(message);
    } finally {
      setSubmitting(false);
    }
  };

  const handleBack = () => {
    setAppPhase('landing');
    navigate('/landing');
  };

  return {
    activePersona, config,
    companyName, companyUrl, uploadedFiles,
    suggestions, showDropdown, activeIndex,
    inputRef, dropdownRef, fileInputRef,
    nameId, urlId, fileId,
    canSubmit, submitting, submitError,
    isCompanyTaken, existingCompanies,
    handleNameChange, selectSuggestion, handleKeyDown,
    handleFileChange, removeFile, handleSubmit, handleBack,
    setShowDropdown, setCompanyUrl, handleInputFocus,
  };
}
