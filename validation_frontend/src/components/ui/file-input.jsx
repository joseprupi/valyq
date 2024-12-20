import React from 'react';
import { Tooltip } from './tooltip';
import { HelpCircle } from './icons/HelpCircle';

export const FileInput = ({ label, id, name, tooltip, value, onChange, disabled }) => {
  return (
    <div className="bg-white rounded-lg p-4 border border-gray-200 hover:border-gray-300 transition-colors">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <label className="text-base font-medium text-gray-900">{label}</label>
          <Tooltip content={tooltip}>
            <HelpCircle className="h-4 w-4 text-gray-400 hover:text-gray-600" />
          </Tooltip>
        </div>
      </div>
      
      <div className="relative">
        <button
          type="button"
          disabled={disabled}
          onClick={() => document.getElementById(id).click()}
          className={`
            w-full h-20 border-2 border-dashed rounded-lg
            flex items-center justify-center gap-3
            transition-colors relative
            ${disabled 
              ? 'border-gray-200 bg-gray-50 cursor-not-allowed' 
              : 'border-gray-300 hover:border-gray-400 cursor-pointer'
            }
          `}
        >
          <svg className="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
              d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
          </svg>
          <span className="text-sm text-gray-600">
            {value ? 'Change file' : 'Choose file'}
          </span>
          {value && (
            <div className="absolute right-3 px-3 py-1 bg-gray-100 rounded-full">
              <span className="text-sm font-medium text-gray-700">{value}</span>
            </div>
          )}
        </button>
        <input
          id={id}
          type="file"
          name={name}
          onChange={onChange}
          className="hidden"
          disabled={disabled}
        />
      </div>
    </div>
  );
};

