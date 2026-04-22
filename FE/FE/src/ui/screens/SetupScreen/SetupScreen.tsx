import { useEffect } from 'react';
import { Link, Building2, ArrowRight, ArrowLeft, Search, Upload, X, FileText } from 'lucide-react';
import { useSetupVM } from './SetupScreen.vm.ts';
import { TopBar } from '../../reusables/TopBar/TopBar.tsx';
import './SetupScreen.css';

export function SetupScreen() {
  const vm = useSetupVM();

  // Close dropdown on outside click
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (
        vm.dropdownRef.current &&
        !vm.dropdownRef.current.contains(e.target as Node) &&
        !vm.inputRef.current?.contains(e.target as Node)
      ) {
        vm.setShowDropdown(false);
      }
    }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, [vm]);

  return (
    <div className="setup-root">
      <TopBar />
      <main className="setup-body">
        <div className="setup-inner">
          <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '1rem' }}>
            <button className="setup-back-btn" onClick={vm.handleBack} aria-label="Go back to analyses">
              <ArrowLeft size={14} strokeWidth={1.5} aria-hidden="true" />
              Back
            </button>
          </div>

          <header className="setup-header">
            <h1 className="setup-title">
              Welcome to {vm.activePersona.name.replace(/\s*Analyst$/, '')}<br />Deal Intelligence
            </h1>
            <p className="setup-subtitle">{vm.config.description}</p>
          </header>

          <div className="setup-card">
            <form className="setup-form" onSubmit={vm.handleSubmit} noValidate>
              {/* Company Name */}
              <div className="setup-field">
                <label htmlFor={vm.nameId} className="setup-label">
                  <Building2 size={14} strokeWidth={1.5} aria-hidden="true" />
                  Company Name <span aria-hidden="true" style={{ color: '#ef4444' }}>*</span>
                </label>
                <div className="setup-input-wrap">
                  <Search size={14} className="setup-input-icon" aria-hidden="true" />
                  <input
                    id={vm.nameId}
                    ref={vm.inputRef}
                    type="text"
                    value={vm.companyName}
                    onChange={(e) => vm.handleNameChange(e.target.value)}
                    onKeyDown={vm.handleKeyDown}
                    onFocus={vm.handleInputFocus}
                    placeholder="Search by company name or ticker..."
                    autoComplete="off"
                    required
                    aria-required="true"
                    aria-autocomplete="list"
                    aria-expanded={vm.showDropdown}
                    aria-haspopup="listbox"
                    className="setup-input"
                    autoFocus
                  />
                  {vm.showDropdown && (
                    <div ref={vm.dropdownRef} className="setup-dropdown" role="listbox" aria-label="Company suggestions">
                      {vm.suggestions.map((s, i) => {
                        const isTaken = vm.existingCompanies.has(s.name.toLowerCase());
                        return (
                        <button
                          key={s.ticker}
                          type="button"
                          role="option"
                          aria-selected={i === vm.activeIndex}
                          aria-disabled={isTaken}
                          onMouseDown={() => vm.selectSuggestion(s)}
                          className={`setup-dropdown-item${i === vm.activeIndex ? ' setup-dropdown-item--active' : ''}${isTaken ? ' setup-dropdown-item--disabled' : ''}`}
                          style={isTaken ? { opacity: 0.4, cursor: 'not-allowed' } : undefined}
                        >
                          <span className="setup-dropdown-ticker">{s.ticker}</span>
                          <span className="setup-dropdown-name">{s.name}{isTaken ? ' (already exists)' : ''}</span>
                        </button>
                        );
                      })}
                    </div>
                  )}
                </div>
              </div>

              {/* IR URL */}
              <div className="setup-field">
                <label htmlFor={vm.urlId} className="setup-label">
                  <Link size={14} strokeWidth={1.5} aria-hidden="true" />
                  Investor Relations URL <span aria-hidden="true" style={{ color: '#ef4444' }}>*</span>
                </label>
                <input
                  id={vm.urlId}
                  type="url"
                  value={vm.companyUrl}
                  onChange={(e) => vm.setCompanyUrl(e.target.value)}
                  placeholder={vm.config.urlPlaceholder}
                  required
                  aria-required="true"
                  className="setup-input-plain"
                />
              </div>

              {/* File Upload */}
              <div className="setup-field">
                <label htmlFor={vm.fileId} className="setup-label">
                  <Upload size={14} strokeWidth={1.5} aria-hidden="true" />
                  Upload Documents
                  <span style={{ color: '#475569', marginLeft: '0.25rem' }}>(optional)</span>
                </label>
                <div
                  className="setup-upload-zone"
                  onClick={() => vm.fileInputRef.current?.click()}
                  onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); vm.fileInputRef.current?.click(); } }}
                  tabIndex={0}
                  role="button"
                  aria-label="Click to upload documents or press Enter"
                >
                  <div className="setup-upload-inner">
                    <Upload size={20} style={{ color: '#475569', margin: '0 auto' }} aria-hidden="true" />
                    <p className="setup-upload-text">Click to upload or drag files here</p>
                    <p className="setup-upload-hint">PDF, DOCX, XLSX, TXT</p>
                  </div>
                  <input
                    id={vm.fileId}
                    ref={vm.fileInputRef}
                    type="file"
                    multiple
                    accept=".pdf,.docx,.xlsx,.txt"
                    onChange={vm.handleFileChange}
                    style={{ display: 'none' }}
                    aria-label="Upload documents"
                  />
                </div>

                {vm.uploadedFiles.length > 0 && (
                  <ul className="setup-file-list" aria-label="Uploaded files">
                    {vm.uploadedFiles.map((file, i) => (
                      <li key={i} className="setup-file-item">
                        <FileText size={14} style={{ color: '#64748b', flexShrink: 0 }} aria-hidden="true" />
                        <span className="setup-file-name">{file.name}</span>
                        <button
                          type="button"
                          className="setup-file-remove"
                          onClick={() => vm.removeFile(i)}
                          aria-label={`Remove ${file.name}`}
                        >
                          <X size={14} strokeWidth={1.5} />
                        </button>
                      </li>
                    ))}
                  </ul>
                )}
              </div>

              {/* Documents to be processed */}
              <div className="setup-docs-box" aria-label="Documents that will be processed">
                <p className="setup-docs-label">Documents to be processed</p>
                <ul className="setup-docs-list">
                  {vm.config.documents.map((item) => (
                    <li key={item} className="setup-docs-item">
                      <span className="setup-docs-dot" aria-hidden="true" />
                      {item}
                    </li>
                  ))}
                </ul>
              </div>

              {vm.isCompanyTaken && (
                <p className="setup-submit-error" role="alert">
                  An analysis for &quot;{vm.companyName.trim()}&quot; already exists. Please select a different company.
                </p>
              )}

              {vm.submitError && (
                <p className="setup-submit-error" role="alert">
                  {vm.submitError}
                </p>
              )}

              <button
                type="submit"
                disabled={!vm.canSubmit}
                className="setup-submit-btn"
                aria-disabled={!vm.canSubmit}
              >
                {vm.submitting ? (
                  <span aria-live="polite">Creating Analysis...</span>
                ) : (
                  <>
                    Start Analysis
                    <ArrowRight size={16} strokeWidth={1.5} aria-hidden="true" />
                  </>
                )}
              </button>
            </form>
          </div>
        </div>
      </main>
    </div>
  );
}
