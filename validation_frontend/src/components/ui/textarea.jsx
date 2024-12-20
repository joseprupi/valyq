// src/components/ui/textarea.jsx
export function Textarea({ className = '', ...props }) {
    return (
      <textarea 
        className={`w-full p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${className}`}
        {...props}
      />
    )
  }