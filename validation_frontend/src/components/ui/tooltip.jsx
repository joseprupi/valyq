// components/ui/tooltip.jsx
import React, { useState, useEffect, useRef } from 'react';

const Tooltip = ({ children, content }) => {
  const [isVisible, setIsVisible] = useState(false);
  const tooltipRef = useRef(null);
  const triggerRef = useRef(null);

  useEffect(() => {
    const updatePosition = () => {
      if (!isVisible || !tooltipRef.current || !triggerRef.current) return;

      const trigger = triggerRef.current.getBoundingClientRect();
      const tooltip = tooltipRef.current;
      const scrollY = window.scrollY;

      // Position the tooltip above the trigger element
      tooltip.style.position = 'fixed';
      tooltip.style.left = `${trigger.left + (trigger.width / 2)}px`;
      tooltip.style.top = `${trigger.top + scrollY - 10}px`;
    };

    if (isVisible) {
      updatePosition();
      window.addEventListener('scroll', updatePosition);
      window.addEventListener('resize', updatePosition);
    }

    return () => {
      window.removeEventListener('scroll', updatePosition);
      window.removeEventListener('resize', updatePosition);
    };
  }, [isVisible]);

  return (
    <div className="relative inline-flex">
      <div
        ref={triggerRef}
        onMouseEnter={() => setIsVisible(true)}
        onMouseLeave={() => setIsVisible(false)}
        className="inline-flex items-center"
      >
        {children}
      </div>
      {isVisible && (
        <div
          ref={tooltipRef}
          className="fixed z-50 transform -translate-x-1/2 -translate-y-full"
          style={{ pointerEvents: 'none' }}
        >
          <div className="bg-gray-900 text-white px-3 py-2 rounded-md shadow-lg text-sm">
            <div className="relative max-w-xs">
              {content}
              <div 
                className="absolute top-full left-1/2 -translate-x-1/2 border-[6px] border-transparent border-t-gray-900"
                style={{ 
                  width: 0,
                  height: 0
                }}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export { Tooltip };