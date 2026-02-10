'use client';

import React, { useState } from 'react';

interface PaperUploadProps {
  onPapersSubmit: (papers: Array<{type: 'arxiv' | 'doi' | 'pdf', value: string} | File>, includeIntermediate: boolean) => void;
  isLoading?: boolean;
}

export default function PaperUpload({ onPapersSubmit, isLoading = false }: PaperUploadProps) {
  const [inputMethod, setInputMethod] = useState<'links' | 'pdf'>('links');
  const [linksText, setLinksText] = useState('');
  const [files, setFiles] = useState<File[]>([]);
  const [includeIntermediate, setIncludeIntermediate] = useState(true);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files) {
      const fileList = Array.from(event.target.files);
      setFiles(fileList);
    }
  };

  const parseLinks = (text: string): Array<{type: 'arxiv' | 'doi', value: string}> => {
    const lines = text.split('\n').filter(line => line.trim());
    const papers: Array<{type: 'arxiv' | 'doi', value: string}> = [];
    
    for (const line of lines) {
      const trimmed = line.trim();
      
      // ArXiv patterns
      if (trimmed.includes('arxiv.org')) {
        const match = trimmed.match(/(?:arxiv\.org\/abs\/|arxiv\.org\/pdf\/)?([\d.]+)/);
        if (match) {
          papers.push({ type: 'arxiv', value: match[1] });
          continue;
        }
      }
      
      // Standalone ArXiv ID (e.g., 2301.12345)
      if (/^\d{4}\.\d{4,5}(v\d+)?$/.test(trimmed)) {
        papers.push({ type: 'arxiv', value: trimmed.replace(/v\d+$/, '') });
        continue;
      }
      
      // DOI patterns
      if (trimmed.includes('doi.org/') || trimmed.startsWith('10.')) {
        const match = trimmed.match(/(?:doi\.org\/)?(10\.\d+\/[^\s]+)/);
        if (match) {
          papers.push({ type: 'doi', value: match[1] });
          continue;
        }
      }
    }
    
    return papers;
  };

  const handleSubmit = () => {
    if (inputMethod === 'links') {
      const papers = parseLinks(linksText);
      if (papers.length > 0) {
        onPapersSubmit(papers, includeIntermediate);
      }
    } else {
      if (files.length > 0) {
        onPapersSubmit(files, includeIntermediate);
      }
    }
  };

  const handleClear = () => {
    setFiles([]);
    setLinksText('');
  };

  const parsedCount = inputMethod === 'links' ? parseLinks(linksText).length : files.length;

  return (
    <div className="glass rounded-2xl p-6 shadow-2xl border border-white/10">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 animated-gradient rounded-xl flex items-center justify-center">
          <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
          </svg>
        </div>
        <h3 className="text-xl font-bold text-white">Add Papers</h3>
      </div>
      
      <div className="space-y-5">
        {/* Modern tab selector */}
        <div className="flex gap-2 p-1.5 glass-dark rounded-xl">
          <button
            onClick={() => setInputMethod('links')}
            disabled={isLoading}
            className={`flex-1 px-5 py-3 rounded-lg font-bold transition-all ${
              inputMethod === 'links'
                ? 'animated-gradient text-white shadow-lg scale-105'
                : 'text-slate-400 hover:text-white hover:bg-white/5'
            }`}
          >
            ArXiv / DOI
          </button>
          <button
            onClick={() => setInputMethod('pdf')}
            disabled={isLoading}
            className={`flex-1 px-5 py-3 rounded-lg font-bold transition-all ${
              inputMethod === 'pdf'
                ? 'animated-gradient text-white shadow-lg scale-105'
                : 'text-slate-400 hover:text-white hover:bg-white/5'
            }`}
          >
            PDF Files
          </button>
        </div>

        {/* Links input */}
        {inputMethod === 'links' && (
          <div className="space-y-3">
            <textarea
              value={linksText}
              onChange={(e) => setLinksText(e.target.value)}
              disabled={isLoading}
              placeholder="Paste ArXiv URLs or DOIs (one per line):

https://arxiv.org/abs/2301.12345
2301.12345
10.1234/example.doi"
              className="w-full h-48 px-4 py-4 glass-dark text-slate-200 placeholder-slate-500 rounded-xl font-mono text-sm resize-none focus:ring-2 focus:ring-blue-500 border border-white/10 focus:border-blue-500/50 transition-all"
            />
            {parsedCount > 0 && (
              <div className="flex items-center gap-2 px-4 py-2 bg-green-500/10 border border-green-500/20 rounded-lg">
                <svg className="w-5 h-5 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                <span className="text-green-300 font-medium">
                  Detected {parsedCount} paper{parsedCount > 1 ? 's' : ''}
                </span>
              </div>
            )}
          </div>
        )}

        {/* PDF upload */}
        {inputMethod === 'pdf' && (
          <div className="space-y-4">
            <label
              htmlFor="file-upload"
              className="block w-full px-6 py-10 border-2 border-dashed border-white/20 rounded-xl text-center cursor-pointer hover:border-blue-500/50 hover:bg-white/5 transition-all group"
            >
              <div className="space-y-3">
                <div className="mx-auto w-16 h-16 bg-blue-500/10 rounded-full flex items-center justify-center group-hover:scale-110 transition-transform">
                  <svg className="w-8 h-8 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                </div>
                <div>
                  <span className="font-bold text-blue-400">Click to upload</span>
                  <span className="text-slate-400"> or drag and drop</span>
                </div>
                <p className="text-sm text-slate-500">PDF files only</p>
              </div>
              <input
                id="file-upload"
                type="file"
                className="sr-only"
                multiple
                accept=".pdf"
                onChange={handleFileChange}
                disabled={isLoading}
              />
            </label>

            {files.length > 0 && (
              <div className="space-y-2">
                <div className="text-sm font-bold text-slate-300">
                  Selected files ({files.length}):
                </div>
                <div className="max-h-40 overflow-y-auto space-y-2">
                  {files.map((file, index) => (
                    <div
                      key={index}
                      className="text-xs text-slate-300 glass-dark px-4 py-3 rounded-lg border border-white/10"
                    >
                      <div className="font-medium">{file.name}</div>
                      <div className="text-slate-500 mt-1">{(file.size / 1024 / 1024).toFixed(2)} MB</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Intermediate papers option */}
        <div className="glass-dark rounded-xl p-4 border border-white/10">
          <label className="flex items-start gap-3 cursor-pointer group">
            <input
              type="checkbox"
              checked={includeIntermediate}
              onChange={(e) => setIncludeIntermediate(e.target.checked)}
              className="mt-1 w-5 h-5 rounded border-white/20 bg-white/10 text-blue-500 focus:ring-2 focus:ring-blue-500"
              disabled={isLoading}
            />
            <div className="flex-1">
              <div className="font-bold text-white group-hover:text-blue-400 transition-colors">
                Include intermediate papers
              </div>
              <div className="text-sm text-slate-400 mt-1">
                Fetch papers that connect your selection through citations (adds 50-100+ papers)
              </div>
            </div>
          </label>
        </div>

        {/* Action buttons */}
        <div className="flex gap-3">
          <button
            onClick={handleSubmit}
            disabled={parsedCount === 0 || isLoading}
            className="flex-1 px-6 py-4 animated-gradient text-white font-bold rounded-xl shadow-2xl hover:scale-105 disabled:opacity-50 disabled:hover:scale-100 disabled:cursor-not-allowed transition-all"
          >
            {isLoading ? (
              <div className="flex items-center justify-center gap-3">
                <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Building Graph...
              </div>
            ) : (
              'Build Graph'
            )}
          </button>
          {parsedCount > 0 && (
            <button
              onClick={handleClear}
              disabled={isLoading}
              className="px-6 py-4 glass text-slate-300 hover:text-white font-bold rounded-xl hover:bg-white/10 disabled:opacity-50 transition-all"
            >
              Clear
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
