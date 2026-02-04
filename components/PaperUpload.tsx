'use client';

import React, { useState } from 'react';

interface PaperUploadProps {
  onFilesSelected: (files: File[], includeIntermediate: boolean) => void;
  isLoading?: boolean;
}

export default function PaperUpload({ onFilesSelected, isLoading = false }: PaperUploadProps) {
  const [files, setFiles] = useState<File[]>([]);
  const [includeIntermediate, setIncludeIntermediate] = useState(true);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files) {
      const fileList = Array.from(event.target.files);
      setFiles(fileList);
    }
  };

  const handleSubmit = () => {
    if (files.length > 0) {
      onFilesSelected(files, includeIntermediate);
    }
  };

  const handleClear = () => {
    setFiles([]);
  };

  return (
    <div className="w-full p-6 bg-white rounded-lg border border-gray-200 shadow-sm">
      <h3 className="text-lg font-semibold mb-4">Upload Papers</h3>
      
      <div className="space-y-4">
        {/* File input */}
        <div>
          <label
            htmlFor="file-upload"
            className="block w-full px-4 py-6 border-2 border-dashed border-gray-300 rounded-lg text-center cursor-pointer hover:border-blue-500 transition-colors"
          >
            <div className="space-y-2">
              <svg
                className="mx-auto h-12 w-12 text-gray-400"
                stroke="currentColor"
                fill="none"
                viewBox="0 0 48 48"
                aria-hidden="true"
              >
                <path
                  d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                  strokeWidth={2}
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
              <div className="text-sm text-gray-600">
                <span className="font-medium text-blue-600">Click to upload</span> or drag and drop
              </div>
              <p className="text-xs text-gray-500">PDF files only</p>
            </div>
            <input
              id="file-upload"
              name="file-upload"
              type="file"
              className="sr-only"
              multiple
              accept=".pdf"
              onChange={handleFileChange}
              disabled={isLoading}
            />
          </label>
        </div>

        {/* Selected files */}
        {files.length > 0 && (
          <div className="space-y-2">
            <div className="text-sm font-medium text-gray-700">
              Selected files ({files.length}):
            </div>
            <div className="max-h-40 overflow-y-auto space-y-1">
              {files.map((file, index) => (
                <div
                  key={index}
                  className="text-xs text-gray-600 bg-gray-50 px-3 py-2 rounded border border-gray-200"
                >
                  {file.name} <span className="text-gray-400">({(file.size / 1024 / 1024).toFixed(2)} MB)</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Intermediate papers option */}
        <div className="border-t border-gray-200 pt-4">
          <label className="flex items-start space-x-3 cursor-pointer">
            <input
              type="checkbox"
              checked={includeIntermediate}
              onChange={(e) => setIncludeIntermediate(e.target.checked)}
              className="mt-1"
              disabled={isLoading}
            />
            <div className="flex-1">
              <div className="text-sm font-medium text-gray-900">
                Include intermediate papers
              </div>
              <div className="text-xs text-gray-500 mt-1">
                Fetch papers that connect your uploaded papers through citations.
                This can add 50-100+ papers to show the full citation network.
              </div>
            </div>
          </label>
        </div>

        {/* Actions */}
        <div className="flex gap-2">
          <button
            onClick={handleSubmit}
            disabled={files.length === 0 || isLoading}
            className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors font-medium"
          >
            {isLoading ? 'Building Graph...' : 'Build Graph'}
          </button>
          {files.length > 0 && (
            <button
              onClick={handleClear}
              disabled={isLoading}
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 disabled:bg-gray-100 disabled:cursor-not-allowed transition-colors"
            >
              Clear
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
