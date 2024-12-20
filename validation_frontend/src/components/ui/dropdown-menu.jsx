import React, { useState, useRef, useEffect } from 'react';

const DropdownMenu = ({ children, className = '' }) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div ref={dropdownRef} className={`relative inline-block ${className}`}>
      {React.Children.map(children, child => {
        if (child.type.displayName === 'DropdownTrigger') {
          return React.cloneElement(child, {
            onClick: () => setIsOpen(!isOpen),
            'aria-expanded': isOpen
          });
        }
        if (child.type.displayName === 'DropdownContent') {
          return isOpen ? React.cloneElement(child) : null;
        }
        return child;
      })}
    </div>
  );
};

const DropdownTrigger = ({ children, onClick, className = '', ...props }) => (
  <button
    type="button"
    onClick={onClick}
    className={`inline-flex items-center justify-center ${className}`}
    {...props}
  >
    {children}
  </button>
);
DropdownTrigger.displayName = 'DropdownTrigger';

const DropdownContent = ({ children, align = 'start', className = '' }) => {
  const alignmentClasses = {
    start: 'left-0',
    end: 'right-0'
  };

  return (
    <div className={`
      absolute z-50 mt-1 min-w-[8rem]
      bg-white rounded-md shadow-lg border border-gray-200
      py-1 ${alignmentClasses[align]} ${className}
    `}>
      {children}
    </div>
  );
};
DropdownContent.displayName = 'DropdownContent';

const DropdownItem = ({ children, onClick, className = '', disabled = false }) => (
  <button
    type="button"
    onClick={onClick}
    disabled={disabled}
    className={`
      w-full text-left px-4 py-2 text-sm
      hover:bg-gray-100 disabled:opacity-50
      disabled:cursor-not-allowed flex items-center
      ${className}
    `}
  >
    {children}
  </button>
);

const DropdownLabel = ({ children, className = '' }) => (
  <div className={`px-4 py-2 text-sm font-semibold text-gray-700 ${className}`}>
    {children}
  </div>
);

const DropdownSeparator = ({ className = '' }) => (
  <div className={`h-px my-1 bg-gray-200 ${className}`} />
);

export {
  DropdownMenu,
  DropdownTrigger,
  DropdownContent,
  DropdownItem,
  DropdownLabel,
  DropdownSeparator
};