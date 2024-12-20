import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import rehypeRaw from 'rehype-raw';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import './TestResultRenderer.css';

const TestResultRenderer = ({ results, testCode }) => {
  const [activeTab, setActiveTab] = useState('results');
  const [imageErrors, setImageErrors] = useState({});

  const handleImageError = (imageUrl) => {
    setImageErrors(prev => ({
      ...prev,
      [imageUrl]: true
    }));
  };

  return (
    <div className="test-results-container">
      <div className="tabs">
        <button 
          className={`tab ${activeTab === 'results' ? 'active' : ''}`}
          onClick={() => setActiveTab('results')}
        >
          Test Results
        </button>
        <button 
          className={`tab ${activeTab === 'code' ? 'active' : ''}`}
          onClick={() => setActiveTab('code')}
        >
          Test Code
        </button>
      </div>

      <div className="tab-content">
        {activeTab === 'results' && (
          <div className="test-results">
            {results.map((result, index) => (
              <div key={index} className="result-section">
                <h5 className="result-filename">{result.filename}</h5>
                <div className="markdown-content">
                  <ReactMarkdown 
                    remarkPlugins={[remarkGfm]}
                    rehypePlugins={[rehypeRaw]}
                    components={{
                      img: ({node, src, alt, ...props}) => {
                        if (imageErrors[src]) {
                          return (
                            <div className="image-error">
                              Failed to load image: {alt}
                            </div>
                          );
                        }
                        return (
                          <img 
                            src={src}
                            alt={alt || ''}
                            onError={() => handleImageError(src)}
                            className="markdown-image"
                            {...props}
                          />
                        );
                      },
                      table: ({node, ...props}) => (
                        <div className="table-container">
                          <table {...props} className="markdown-table" />
                        </div>
                      ),
                      code: ({node, inline, className, children, ...props}) => {
                        if (inline) {
                          return <code className="inline-code" {...props}>{children}</code>;
                        }
                        const language = className ? className.replace('language-', '') : 'text';
                        return (
                          <SyntaxHighlighter
                            language={language}
                            style={oneDark}
                            className="code-block"
                            {...props}
                          >
                            {String(children)}
                          </SyntaxHighlighter>
                        );
                      }
                    }}
                  >
                    {result.content}
                  </ReactMarkdown>
                </div>
              </div>
            ))}
          </div>
        )}

        {activeTab === 'code' && (
          <div className="test-code">
            <SyntaxHighlighter
              language="python"
              style={oneDark}
              showLineNumbers={true}
              wrapLines={true}
              customStyle={{
                margin: 0,
                borderRadius: '4px',
                fontSize: '14px',
              }}
            >
              {testCode || '# No test code available'}
            </SyntaxHighlighter>
          </div>
        )}
      </div>
    </div>
  );
};

export default TestResultRenderer;