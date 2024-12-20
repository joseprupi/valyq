import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import rehypeRaw from 'rehype-raw';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import './TestConversation.css';

const TestConversation = ({ test, onSubmitFollowUp }) => {
  const [followUpMessage, setFollowUpMessage] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [activeTab, setActiveTab] = useState('results');
  const [imageErrors, setImageErrors] = useState({});

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Don't submit if empty
    if (!followUpMessage.trim()) return;
    
    setSubmitting(true);
    const messageToSend = followUpMessage.trim();
    
    try {
      await onSubmitFollowUp(messageToSend);
      // Only clear on success
      setFollowUpMessage('');
    } catch (error) {
      console.error('Error submitting follow-up:', error);
      // Show error to user
      alert('Failed to send follow-up message. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleImageError = (imageUrl) => {
    setImageErrors(prev => ({
      ...prev,
      [imageUrl]: true
    }));
  };

  return (
    <div className="test-conversation">
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
        {activeTab === 'results' && test.results && (
          <div className="results">
            {test.results.map((result, idx) => (
              <div key={idx} className="result-item">
                <h4>{result.filename}</h4>
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
          <div className="code-view">
            <SyntaxHighlighter
              language="python"
              style={oneDark}
              showLineNumbers={true}
              customStyle={{
                margin: 0,
                borderRadius: '4px',
                fontSize: '14px'
              }}
            >
              {test.testCode || '# No test code available'}
            </SyntaxHighlighter>
          </div>
        )}
      </div>

      {test.conversation?.messages && (
        <div className="conversation-history">
        <h4>Conversation History</h4>
        {test.conversation?.messages && test.conversation.messages.map((message, index) => (
          <div 
            key={index} 
            className={`message ${message.role}`}
          >
            <div className="message-header">
              {message.role === 'user' ? 'You' : 'Assistant'}
            </div>
            <div className="message-content">
              <ReactMarkdown>
                {message.content}
              </ReactMarkdown>
            </div>
          </div>
        ))}
        {followUpMessage && (  // Show current follow-up being typed
          <div className="message user pending">
            <div className="message-header">You (typing)</div>
            <div className="message-content">{followUpMessage}</div>
          </div>
        )}
      </div>
      )}

<form onSubmit={handleSubmit} className="follow-up-form">
        <textarea
          value={followUpMessage}
          onChange={(e) => setFollowUpMessage(e.target.value)}
          placeholder="Enter follow-up message to improve the test..."
          className="follow-up-input"
          disabled={submitting}
        />
        <button 
          type="submit" 
          disabled={!followUpMessage.trim() || submitting}
          className="button"
        >
          {submitting ? 'Sending...' : 'Send Follow-up'}
        </button>
      </form>
    </div>
  );
};

export default TestConversation;