const FileInput = ({ label, id, name, tooltip, value, onChange, disabled }) => {
    return (
      <div className="bg-white rounded-lg p-6 border border-gray-200 hover:border-gray-300 transition-colors">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <label className="text-lg font-medium text-gray-900">{label}</label>
            <Tooltip content={tooltip}>
              <HelpCircle className="h-4 w-4 text-gray-400 hover:text-gray-600" />
            </Tooltip>
          </div>
          {value && (
            <span className="text-sm text-gray-600">{value}</span>
          )}
        </div>
        
        <div className="mt-2">
          <button
            type="button"
            disabled={disabled}
            onClick={() => document.getElementById(id).click()}
            className={`
              w-full h-32 border-2 border-dashed rounded-lg
              flex flex-col items-center justify-center gap-2
              transition-colors
              ${disabled 
                ? 'border-gray-200 bg-gray-50 cursor-not-allowed' 
                : 'border-gray-300 hover:border-gray-400 cursor-pointer'
              }
            `}
          >
            <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            <span className="text-sm text-gray-600">
              {value ? 'Change file' : 'Choose file'}
            </span>
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