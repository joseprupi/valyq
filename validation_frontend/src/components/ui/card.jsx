// src/components/ui/card.jsx
export function Card({ children, className = '' }) {
    return (
      <div className={`bg-white shadow-lg rounded-lg p-6 ${className}`}>
        {children}
      </div>
    )
  }