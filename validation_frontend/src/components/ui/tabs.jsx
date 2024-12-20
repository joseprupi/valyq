// src/components/ui/tabs.jsx
import React, { createContext, useContext } from 'react';

const TabsContext = createContext({
  activeTab: '',
  setActiveTab: () => {} 
});

function Tabs({ children, value = '', onValueChange }) {
  return (
    <TabsContext.Provider value={{ activeTab: value, setActiveTab: onValueChange }}>
      {children}
    </TabsContext.Provider>
  );
}

function TabsList({ children }) {
  return (
    <div className="flex items-center p-1 space-x-1 bg-gray-100/80 rounded-lg">
      {children}
    </div>
  );
}

function TabsTrigger({ children, value }) {
  const { activeTab, setActiveTab } = useContext(TabsContext);
  
  return (
    <button
      type="button"
      onClick={() => setActiveTab(value)}
      className={`
        px-3 py-1.5 text-sm font-medium rounded-md
        transition-all duration-200
        ${activeTab === value 
          ? 'bg-white text-gray-900 shadow-sm' 
          : 'text-gray-600 hover:text-gray-900 hover:bg-white/50'
        }
      `}
    >
      {children}
    </button>
  );
}

function TabsContent({ children, value }) {
  const { activeTab } = useContext(TabsContext);
  if (activeTab !== value) return null;
  return children;
}

export { Tabs, TabsList, TabsTrigger, TabsContent };