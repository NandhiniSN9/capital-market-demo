import { useState, useRef, useEffect } from 'react';
import { Link, Building2, ArrowRight, ArrowLeft, Search, Upload, X, FileText } from 'lucide-react';
import { usePersonaStore } from '@/store/personaStore';
import { getPersonaConfig, ACCENT_CLASSES } from '@/helpers/data/personaConfig';

interface CompanySuggestion {
  name: string;
  ticker: string;
  url: string;
}

const COMPANY_SUGGESTIONS: CompanySuggestion[] = [
  { name: 'Apple Inc.', ticker: 'AAPL', url: 'https://investor.apple.com' },
  { name: 'Microsoft Corporation', ticker: 'MSFT', url: 'https://www.microsoft.com/en-us/investor' },
  { name: 'Alphabet Inc.', ticker: 'GOOGL', url: 'https://abc.xyz/investor' },
  { name: 'Amazon.com Inc.', ticker: 'AMZN', url: 'https://ir.aboutamazon.com' },
  { name: 'NVIDIA Corporation', ticker: 'NVDA', url: 'https://investor.nvidia.com' },
  { name: 'Meta Platforms Inc.', ticker: 'META', url: 'https://investor.fb.com' },
  { name: 'Tesla Inc.', ticker: 'TSLA', url: 'https://ir.tesla.com' },
  { name: 'Berkshire Hathaway', ticker: 'BRK', url: 'https://www.berkshirehathaway.com' },
  { name: 'JPMorgan Chase & Co.', ticker: 'JPM', url: 'https://www.jpmorganchase.com/ir' },
  { name: 'Visa Inc.', ticker: 'V', url: 'https://investor.visa.com' },
  { name: 'Johnson & Johnson', ticker: 'JNJ', url: 'https://investor.jnj.com' },
  { name: 'Walmart Inc.', ticker: 'WMT', url: 'https://stock.walmart.com' },
  { name: 'Exxon Mobil Corporation', ticker: 'XOM', url: 'https://ir.exxonmobil.com' },
  { name: 'UnitedHealth Group', ticker: 'UNH', url: 'https://www.unitedhealthgroup.com/investors' },
  { name: 'Mastercard Incorporated', ticker: 'MA', url: 'https://investor.mastercard.com' },
  { name: 'Procter & Gamble Co.', ticker: 'PG', url: 'https://pginvestor.com' },
  { name: 'Home Depot Inc.', ticker: 'HD', url: 'https://ir.homedepot.com' },
  { name: 'Chevron Corporation', ticker: 'CVX', url: 'https://www.chevron.com/investors' },
  { name: 'AbbVie Inc.', ticker: 'ABBV', url: 'https://investors.abbvie.com' },
  { name: 'Costco Wholesale Corporation', ticker: 'COST', url: 'https://investor.costco.com' },
  { name: 'Netflix Inc.', ticker: 'NFLX', url: 'https://ir.netflix.net' },
  { name: 'Salesforce Inc.', ticker: 'CRM', url: 'https://investor.salesforce.com' },
  { name: 'Adobe Inc.', ticker: 'ADBE', url: 'https://www.adobe.com/investor-relations' },
  { name: 'Advanced Micro Devices', ticker: 'AMD', url: 'https://ir.amd.com' },
  { name: 'Intel Corporation', ticker: 'INTC', url: 'https://www.intc.com' },
  { name: 'Qualcomm Incorporated', ticker: 'QCOM', url: 'https://investor.qualcomm.com' },
  { name: 'Goldman Sachs Group', ticker: 'GS', url: 'https://www.goldmansachs.com/investor-relations' },
  { name: 'Morgan Stanley', ticker: 'MS', url: 'https://www.morganstanley.com/about-us-ir' },
  { name: 'Bank of America', ticker: 'BAC', url: 'https://investor.bankofamerica.com' },
  { name: 'Pfizer Inc.', ticker: 'PFE', url: 'https://www.pfizer.com/investors' },
  { name: 'Eli Lilly and Company', ticker: 'LLY', url: 'https://investor.lilly.com' },
  { name: 'Merck & Co. Inc.', ticker: 'MRK', url: 'https://www.merck.com/investor-relations' },
  { name: 'Walt Disney Company', ticker: 'DIS', url: 'https://thewaltdisneycompany.com/investor-relations' },
  { name: 'Comcast Corporation', ticker: 'CMCSA', url: 'https://corporate.comcast.com/investors' },
  { name: 'Verizon Communications', ticker: 'VZ', url: 'https://www.verizon.com/about/investors' },
  { name: 'AT&T Inc.', ticker: 'T', url: 'https://investors.att.com' },
  { name: 'Boeing Company', ticker: 'BA', url: 'https://investors.boeing.com' },
  { name: 'Caterpillar Inc.', ticker: 'CAT', url: 'https://www.caterpillar.com/investors' },
  { name: 'Deere & Company', ticker: 'DE', url: 'https://www.deere.com/en/our-company/investor-relations' },
  { name: 'Lockheed Martin', ticker: 'LMT', url: 'https://www.lockheedmartin.com/investors' },
  { name: 'Raytheon Technologies', ticker: 'RTX', url: 'https://www.rtx.com/investors' },
  { name: 'Honeywell International', ticker: 'HON', url: 'https://www.honeywell.com/us/en/investors' },
  { name: 'Thermo Fisher Scientific', ticker: 'TMO', url: 'https://ir.thermofisher.com' },
  { name: 'Danaher Corporation', ticker: 'DHR', url: 'https://www.danaher.com/investors' },
  { name: 'S&P Global Inc.', ticker: 'SPGI', url: 'https://investor.spglobal.com' },
  { name: 'BlackRock Inc.', ticker: 'BLK', url: 'https://ir.blackrock.com' },
  { name: 'Pepsico Inc.', ticker: 'PEP', url: 'https://www.pepsico.com/investors' },
  { name: 'Coca-Cola Company', ticker: 'KO', url: 'https://investors.coca-colacompany.com' },
  { name: "McDonald's Corporation", ticker: 'MCD', url: 'https://corporate.mcdonalds.com/corpmcd/investors' },
  { name: 'Starbucks Corporation', ticker: 'SBUX', url: 'https://investor.starbucks.com' },
];

function filterSuggestions(query: string): CompanySuggestion[] {
  if (!query.trim()) return [];
  const q = query.toLowerCase();
  return COMPANY_SUGGESTIONS.filter(
    (c) =>
      c.name.toLowerCase().includes(q) ||
      c.ticker.toLowerCase().includes(q)
  ).slice(0, 6);
}

export function PersonaSetup() {
  const [companyName, setCompanyName] = useState('');
  const [companyUrl, setCompanyUrl] = useState('');
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);
  const [suggestions, setSuggestions] = useState<CompanySuggestion[]>([]);
  const [showDropdown, setShowDropdown] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const inputRef = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const activePersona = usePersonaStore((s) => s.activePersona);
  const submitSetup = usePersonaStore((s) => s.submitSetup);
  const setAppPhase = usePersonaStore((s) => s.setAppPhase);

  const config = getPersonaConfig(activePersona.id);
  const accent = ACCENT_CLASSES[config.accentColor];

  const canSubmit = companyName.trim().length > 0 && companyUrl.trim().length > 0;

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(e.target as Node) &&
        !inputRef.current?.contains(e.target as Node)
      ) {
        setShowDropdown(false);
      }
    }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  const handleNameChange = (value: string) => {
    setCompanyName(value);
    setActiveIndex(-1);
    const results = filterSuggestions(value);
    setSuggestions(results);
    setShowDropdown(results.length > 0);
  };

  const selectSuggestion = (suggestion: CompanySuggestion) => {
    setCompanyName(suggestion.name);
    setCompanyUrl(suggestion.url);
    setSuggestions([]);
    setShowDropdown(false);
    setActiveIndex(-1);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!showDropdown) return;
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setActiveIndex((i) => Math.min(i + 1, suggestions.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActiveIndex((i) => Math.max(i - 1, 0));
    } else if (e.key === 'Enter' && activeIndex >= 0) {
      e.preventDefault();
      selectSuggestion(suggestions[activeIndex]);
    } else if (e.key === 'Escape') {
      setShowDropdown(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setUploadedFiles((prev) => [...prev, ...Array.from(e.target.files!)]);
    }
  };

  const removeFile = (index: number) => {
    setUploadedFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!canSubmit) return;
    submitSetup({ name: companyName.trim(), url: companyUrl.trim() });
  };

  return (
    <div className="flex h-full overflow-y-auto">
      <div className="m-auto w-full max-w-xl px-8 py-4">
        {/* Back to landing */}
        <div className="flex justify-center mb-4">
          <button
            onClick={() => setAppPhase('landing')}
            className="flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-300 transition-colors"
          >
            <ArrowLeft className="h-3.5 w-3.5 stroke-[1.5]" />
            Back
          </button>
        </div>

        {/* Welcome header */}
        <div className="mb-4 text-center">
          <h2 className="text-3xl font-bold text-white mb-3">
            Welcome to {activePersona.name.replace(/\s*Analyst$/, '')}
            <br />
            Deal Intelligence
          </h2>
          <p className="text-sm text-slate-400 leading-relaxed max-w-md mx-auto">
            {config.description}
          </p>
        </div>

        {/* Form Card */}
        <div className="rounded-2xl border border-slate-800/80 bg-slate-900/60 p-5">
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Company Name with typeahead */}
            <div className="space-y-2">
              <label className="flex items-center gap-1.5 text-xs font-medium text-slate-400">
                <Building2 className="h-3.5 w-3.5 stroke-[1.5]" />
                Company Name
              </label>
              <div className="relative">
                <div className="pointer-events-none absolute inset-y-0 left-3 flex items-center">
                  <Search className="h-3.5 w-3.5 text-slate-500 stroke-[1.5]" />
                </div>
                <input
                  ref={inputRef}
                  type="text"
                  value={companyName}
                  onChange={(e) => handleNameChange(e.target.value)}
                  onKeyDown={handleKeyDown}
                  onFocus={() => {
                    if (suggestions.length > 0) setShowDropdown(true);
                  }}
                  placeholder="Search by company name or ticker..."
                  autoComplete="off"
                  className="w-full rounded-xl border border-slate-700/80 bg-slate-950/80 py-3 pl-9 pr-3.5 text-sm text-slate-100 placeholder:text-slate-500 outline-none focus:border-[#145D70]/60 focus:ring-1 focus:ring-[#145D70]/20 transition-all"
                  autoFocus
                />

                {/* Dropdown */}
                {showDropdown && (
                  <div
                    ref={dropdownRef}
                    className="absolute z-20 mt-1.5 w-full overflow-hidden rounded-xl border border-slate-700 bg-slate-900 shadow-xl shadow-black/40"
                  >
                    {suggestions.map((s, i) => (
                      <button
                        key={s.ticker}
                        type="button"
                        onMouseDown={() => selectSuggestion(s)}
                        className={`flex w-full items-center gap-3 px-3.5 py-2.5 text-left transition-colors ${
                          i === activeIndex
                            ? 'bg-[#145D70]/20 text-[#8DD8EA]'
                            : 'hover:bg-slate-800 text-slate-300'
                        }`}
                      >
                        <span className="flex h-6 w-10 flex-shrink-0 items-center justify-center rounded border border-slate-700 bg-slate-800 text-[10px] font-mono font-semibold text-slate-400">
                          {s.ticker}
                        </span>
                        <span className="text-sm">{s.name}</span>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Investor Relations URL */}
            <div className="space-y-2">
              <label className="flex items-center gap-1.5 text-xs font-medium text-slate-400">
                <Link className="h-3.5 w-3.5 stroke-[1.5]" />
                Investor Relations URL
              </label>
              <input
                type="url"
                value={companyUrl}
                onChange={(e) => setCompanyUrl(e.target.value)}
                placeholder={config.urlPlaceholder}
                className="w-full rounded-xl border border-slate-700/80 bg-slate-950/80 px-3.5 py-3 text-sm text-slate-100 placeholder:text-slate-500 outline-none focus:border-[#145D70]/60 focus:ring-1 focus:ring-[#145D70]/20 transition-all"
              />
            </div>

            {/* Document Upload */}
            <div className="space-y-2">
              <label className="flex items-center gap-1.5 text-xs font-medium text-slate-400">
                <Upload className="h-3.5 w-3.5 stroke-[1.5]" />
                Upload Documents
                <span className="text-slate-600">(optional)</span>
              </label>
              <div
                onClick={() => fileInputRef.current?.click()}
                className="flex cursor-pointer items-center justify-center rounded-xl border border-dashed border-slate-700/80 bg-slate-950/40 px-3.5 py-5 transition-all hover:border-[#145D70]/40 hover:bg-slate-950/60"
              >
                <div className="text-center">
                  <Upload className="mx-auto mb-2 h-5 w-5 text-slate-500 stroke-[1.5]" />
                  <p className="text-xs text-slate-400">
                    Click to upload or drag files here
                  </p>
                  <p className="mt-1 text-[10px] text-slate-600">
                    PDF, DOCX, XLSX, TXT
                  </p>
                </div>
                <input
                  ref={fileInputRef}
                  type="file"
                  multiple
                  accept=".pdf,.docx,.xlsx,.txt"
                  onChange={handleFileChange}
                  className="hidden"
                />
              </div>

              {uploadedFiles.length > 0 && (
                <div className="space-y-1.5 mt-2">
                  {uploadedFiles.map((file, i) => (
                    <div
                      key={i}
                      className="flex items-center gap-2 rounded-lg border border-slate-800 bg-slate-950/50 px-3 py-2"
                    >
                      <FileText className="h-3.5 w-3.5 flex-shrink-0 text-slate-500 stroke-[1.5]" />
                      <span className="flex-1 truncate text-xs text-slate-300">
                        {file.name}
                      </span>
                      <button
                        type="button"
                        onClick={() => removeFile(i)}
                        className="flex-shrink-0 text-slate-600 hover:text-slate-300 transition-colors"
                      >
                        <X className="h-3.5 w-3.5 stroke-[1.5]" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* What will be processed */}
            <div className="rounded-xl border border-slate-800/60 bg-slate-950/40 px-4 py-3.5">
              <p className="mb-2.5 text-[11px] font-medium text-slate-500 uppercase tracking-wide">
                Documents to be processed
              </p>
              <ul className="space-y-2">
                {config.documents.map((item) => (
                  <li key={item} className="flex items-start gap-2.5 text-xs text-slate-400">
                    <span className="mt-1 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-[#145D70]/70" />
                    {item}
                  </li>
                ))}
              </ul>
            </div>

            {/* Submit */}
            <button
              type="submit"
              disabled={!canSubmit}
              className="group flex w-full items-center justify-center gap-2 rounded-xl bg-[#145D70] px-4 py-3 text-sm font-medium text-white transition-all hover:bg-[#1A7A92] disabled:opacity-40 disabled:cursor-not-allowed"
            >
              Start Analysis
              <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5 stroke-[1.5]" />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
