// MenuBar.jsx
import React from 'react';
import {
    DropdownMenu,
    DropdownTrigger,
    DropdownContent,
    DropdownItem,
    DropdownLabel,
    DropdownSeparator
} from './ui/dropdown-menu';
import { Settings } from './ui/icons';

// Add 'export default' before the component
const MenuBar = ({ onLoadValidation, onGenerateReport, onLogout }) => {
    return (
        <div className="fixed top-0 left-0 right-0 bg-white border-b shadow-sm z-50">
            <div className="container mx-auto px-4">
                <div className="h-16 flex items-center justify-between">
                    {/* Left side with logo and validation menu */}
                    <div className="flex items-center space-x-8">
                        {/* Logo and title */}
                        <div className="flex items-center">
                            <div className="bg-blue-600 text-white p-2 rounded">
                                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                                        d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                            </div>
                            <h1 className="ml-3 text-xl font-semibold text-gray-900">Model Validation Tool</h1>
                        </div>

                        {/* Validation dropdown */}
                        <DropdownMenu>
                            <DropdownTrigger className="px-4 py-2 rounded-md bg-gray-50 hover:bg-gray-100 
                  inline-flex items-center gap-2 transition-colors">
                                <span className="text-gray-700">Validation</span>
                                <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                </svg>
                            </DropdownTrigger>
                            <DropdownContent className="w-56">
                                <DropdownItem onClick={onLoadValidation}>Load Validation</DropdownItem>
                                <DropdownItem onClick={onGenerateReport}>Generate Report</DropdownItem>
                                <DropdownItem>Recent Validations</DropdownItem>
                            </DropdownContent>
                        </DropdownMenu>
                    </div>

                    {/* Right side with settings and user menu */}
                    <div className="flex items-center space-x-4">
                        <DropdownMenu>
                            <DropdownTrigger className="p-2 rounded-full hover:bg-gray-100">
                                <Settings className="w-5 h-5 text-gray-600" />
                            </DropdownTrigger>
                            <DropdownContent align="end" className="w-48">
                                <DropdownLabel>Settings</DropdownLabel>
                                <DropdownSeparator />
                                <DropdownItem>LLM Configuration</DropdownItem>
                                <DropdownItem>App Preferences</DropdownItem>
                                <DropdownItem>User Settings</DropdownItem>
                            </DropdownContent>
                        </DropdownMenu>

                        <DropdownMenu>
                            <DropdownTrigger className="flex items-center space-x-2">
                                <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
                                    <span className="text-white text-sm font-medium">JD</span>
                                </div>
                            </DropdownTrigger>
                            <DropdownContent align="end" className="w-48">
                                <DropdownLabel>User Options</DropdownLabel>
                                <DropdownSeparator />
                                <DropdownItem>Profile</DropdownItem>
                                <DropdownSeparator />
                                <DropdownItem onClick={onLogout} className="text-red-600">Sign Out</DropdownItem>
                            </DropdownContent>
                        </DropdownMenu>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default MenuBar;