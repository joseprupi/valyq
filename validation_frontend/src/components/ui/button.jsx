// src/components/ui/button.jsx
import React from 'react'

export function Button({ children, variant = 'default', ...props }) {
  const styles = {
    default: 'bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded',
    outline: 'border-2 border-blue-500 hover:bg-blue-100 text-blue-500 font-bold py-2 px-4 rounded',
    ghost: 'text-blue-500 hover:bg-blue-100 font-bold py-2 px-4 rounded'
  }

  return (
    <button className={styles[variant]} {...props}>
      {children}
    </button>
  )
}