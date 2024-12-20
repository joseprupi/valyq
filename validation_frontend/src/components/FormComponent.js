import React, { useState } from 'react';

import { Alert } from "./ui/alert"

import { Button } from "./ui/button"

import { Card } from "./ui/card"

import { Download } from 'lucide-react';

import { FileInput } from './ui/file-input';
import { Tabs, TabsList, TabsTrigger, TabsContent } from './ui/tabs';

import { Textarea } from "./ui/textarea"
import { HelpCircle } from "./ui/icons/HelpCircle"

import MenuBar from "./MenuBar";

import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "./ui/tooltip"

import TestConversation from './TestConversation';

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "./ui/alert-dialog"

import { useAuth } from './auth';

const FormComponent = () => {

  const { logout } = useAuth();

  const { token } = useAuth();

  const [formData, setFormData] = useState({
    modelDocumentation: ''
  });
  const [files, setFiles] = useState({
    documentation: null,
    trainingScript: null,
    trainedModel: null,
    trainingDataset: null,
    testDataset: null
  });
  const [fileNames, setFileNames] = useState({
    documentation: '',
    trainingScript: '',
    trainedModel: '',
    trainingDataset: '',
    testDataset: ''
  });
  const [validationId, setValidationId] = useState(null);
  const [executionId, setExecutionId] = useState(null);
  const [isCreating, setIsCreating] = useState(false);
  const [error, setError] = useState('');
  const [status, setStatus] = useState('');
  const [loadValidationId, setLoadValidationId] = useState('');
  const [showLoadForm, setShowLoadForm] = useState(false);
  const [testToDelete, setTestToDelete] = useState(null);
  const [customTests, setCustomTests] = useState([]);
  const [activeTab, setActiveTab] = useState('main');
  const [nextTestId, setNextTestId] = useState(1);
  const [showLoadDialog, setShowLoadDialog] = useState(false);
  const [isGeneratingReport, setIsGeneratingReport] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prevState => ({
      ...prevState,
      [name]: value
    }));
  };

  const handleLoadDialogOpen = () => {
    setShowLoadDialog(true);
  };

  const handleFileChange = (e) => {
    const { name, files: fileList } = e.target;
    if (fileList.length > 0) {
      setFiles(prevState => ({
        ...prevState,
        [name]: fileList[0]
      }));
      setFileNames(prevState => ({
        ...prevState,
        [name]: fileList[0].name
      }));
    }
  };

  const confirmDelete = async () => {
    if (!testToDelete) return;

    if (testToDelete.test_id) {
      // Saved test - delete from backend
      await handleDeleteTest(testToDelete.test_id);
    } else {
      // Unsaved test - remove from state
      setCustomTests(prev => prev.filter(test => test.id !== testToDelete.id));
      setActiveTab('main');
    }
    setTestToDelete(null);
  };

  const handleDeleteTest = async (testId) => {
    if (!testId) return;

    try {
      const response = await fetch(`/test/${validationId}/${testId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      // Remove test from state
      setCustomTests(prev => prev.filter(test => test.test_id !== testId));

      // Switch to main tab
      setActiveTab('main');

      // Show success message
      setStatus('Test deleted successfully');

    } catch (error) {
      setError(`Error deleting test: ${error.message}`);
    }
  };

  const handleLoadValidation = async (e) => {
    e.preventDefault();
    setIsCreating(true);
    setError('');
    setStatus('Loading validation...');
  
    try {
      // First load validation details
      const validationResponse = await fetch(`/load-validation/${loadValidationId}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (!validationResponse.ok) {
        throw new Error(`HTTP error! status: ${validationResponse.status}`);
      }
      const validationResult = await validationResponse.json();
  
      // Then load tests separately
      const testsResponse = await fetch(`/tests/${loadValidationId}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (!testsResponse.ok) {
        throw new Error(`HTTP error! status: ${testsResponse.status}`);
      }
      const tests = await testsResponse.json();
  
      // Update validation state
      setValidationId(validationResult.validation_id);
      setExecutionId(validationResult.execution_id);
      setFileNames(validationResult.files || {
        documentation: '',
        trainingScript: '',
        trainedModel: '',
        trainingDataset: '',
        testDataset: ''
      });
  
      // Load existing tests with correct title mapping
      if (tests.length > 0) {
        const loadedTests = tests.map((testData, index) => ({
          id: index + 1,
          test_id: testData.test_id,
          // Use the original title if available, fall back to a generic title
          title: testData.title || `Test ${testData.test_id}`,
          // Keep the full description
          description: testData.description || '',
          prompt: testData.prompt || '',
          results: testData.results || [],
          testCode: testData.code || '',
          conversation: testData.conversation || { messages: [] },
          isProcessing: false,
          error: ''
        }));
  
        setCustomTests(loadedTests);
        setNextTestId(Math.max(...loadedTests.map(t => t.id), 0) + 1);
      }
  
      setStatus('Validation loaded successfully');
      setShowLoadForm(false);
  
    } catch (err) {
      setError(`Error: ${err.message}`);
      setStatus('Error loading validation');
    } finally {
      setIsCreating(false);
    }
  };

  const handleCreateValidation = async (e) => {
    e.preventDefault();
    setIsCreating(true);
    setError('');
    setStatus('Creating validation...');

    try {
      const formDataToSend = new FormData();
      formDataToSend.append('modelDocumentation', formData.modelDocumentation);

      Object.keys(files).forEach(key => {
        if (files[key]) {
          formDataToSend.append(key, files[key]);
        }
      });

      const response = await fetch('/create-validation', {
        method: 'POST',
        body: formDataToSend,
        headers: {
          'Authorization': `Bearer ${token}` // Add the authorization header
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      setValidationId(result.validation_id);
      setExecutionId(result.execution_id);
      setStatus('Validation created successfully');

    } catch (err) {
      setError(`Error: ${err.message}`);
      setStatus('Error creating validation');
    } finally {
      setIsCreating(false);
    }
  };

  const addCustomTest = () => {
    const newTest = {
      id: nextTestId,
      title: `Custom Test ${nextTestId}`,
      description: '',
      isProcessing: false,
      error: ''
    };
    setCustomTests(prev => [...prev, newTest]);
    setNextTestId(prev => prev + 1);
    setActiveTab(`test-${newTest.id}`);
  };

  const handleTestSubmit = async (testId, followUpMessage = null) => {
    const test = customTests.find(t => t.id === testId);
    if (!test || !validationId) return;

    setCustomTests(prev =>
      prev.map(t => t.id === testId ? { ...t, isProcessing: true, error: '' } : t)
    );

    try {
      const requestBody = {
        validation_id: validationId,
        test_id: test.test_id || testId,
      };

      // Only include description for initial test
      if (!test.test_id) {
        requestBody.description = test.description;
      }

      // Only include follow_up_message if one was provided
      if (followUpMessage) {
        requestBody.follow_up_message = followUpMessage;
      }

      const response = await fetch('/execute-test', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      console.log('Test result received:', result);

      setCustomTests(prev =>
        prev.map(t =>
          t.id === testId
            ? {
              ...t,
              test_id: result.test_id,
              results: result.results,
              testCode: result.testCode,
              conversation: result.conversation,
              isProcessing: false,
              error: ''
            }
            : t
        )
      );
    } catch (error) {
      console.error('Error executing test:', error);
      setCustomTests(prev =>
        prev.map(t => t.id === testId ? { ...t, error: error.message, isProcessing: false } : t)
      );
    }
  };

  const handleTestTitleChange = (testId, value) => {
    setCustomTests(prev =>
      prev.map(test =>
        test.id === testId ? { ...test, title: value } : test
      )
    );
  };

  const handleTestDescriptionChange = (testId, value) => {
    setCustomTests(prev =>
      prev.map(test =>
        test.id === testId ? { ...test, description: value } : test
      )
    );
  };

  const handleGenerateReport = async () => {
    if (!validationId) return;

    try {
      setIsGeneratingReport(true);

      // Make the API request to generate and download the report
      const response = await fetch(`/generate-report/${validationId}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to generate report');
      }

      // Get the blob from the response
      const blob = await response.blob();

      // Create a download link and trigger it
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `validation_report_${validationId}.docx`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      setStatus('Report generated successfully');

    } catch (error) {
      setError(`Error generating report: ${error.message}`);
    } finally {
      setIsGeneratingReport(false);
    }
  };

  // Update existing removeCustomTest function
  const removeCustomTest = (testId) => {
    const test = customTests.find(t => t.id === testId);
    setTestToDelete(test);
  };

  const renderTestTab = (test) => {
    if (!test) return null;

    return (
      <div className="space-y-6">
        <Card className="p-4">
          <input
            type="text"
            value={test.title || ''}
            onChange={(e) => handleTestTitleChange(test.id, e.target.value)}
            className="w-full mb-4 p-2 border rounded"
            placeholder="Enter test title"
          />
          <Textarea
            value={test.description || ''}
            onChange={(e) => handleTestDescriptionChange(test.id, e.target.value)}
            className="min-h-[100px] mb-4"
            placeholder="Describe the test to be performed..."
          />
          <Button
            onClick={() => handleTestSubmit(test.id)}
            disabled={test.isProcessing || !test.description}
          >
            {test.isProcessing ? 'Processing...' : 'Run Test'}
          </Button>
        </Card>

        {test.error && (
          <Alert variant="destructive">
            {test.error}
          </Alert>
        )}

        {test.results && (
          <TestConversation
            test={test}
            onSubmitFollowUp={async (message) => {
              try {
                // No need for artificial Promise here
                setCustomTests(prev =>
                  prev.map(t =>
                    t.id === test.id
                      ? { ...t, isProcessing: true }
                      : t
                  )
                );

                // Pass the message directly to handleTestSubmit
                await handleTestSubmit(test.id, message);
              } catch (error) {
                console.error('Failed to submit follow-up:', error);
                setCustomTests(prev =>
                  prev.map(t =>
                    t.id === test.id
                      ? { ...t, error: error.message, isProcessing: false }
                      : t
                  )
                );
              }
            }}
          />
        )}
      </div>
    );
  };

  return (
    <div className="min-h-screen flex flex-col pb-16">
      <MenuBar
        onLoadValidation={handleLoadDialogOpen}
        onGenerateReport={handleGenerateReport}
        onLogout={logout}
      />

      <div className="flex-1 mt-16">
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <div className="container mx-auto px-4 mb-16">
            <TabsList>
              <TabsTrigger value="main">Main Form</TabsTrigger>
              {customTests.map(test => (
                <div key={test.id} className="inline-flex items-center gap-1">
                  <TabsTrigger value={`test-${test.id}`}>
                    {test.title || `Test ${test.id}`}
                  </TabsTrigger>
                  <button
                    onClick={(e) => {
                      e.preventDefault();
                      e.stopPropagation();
                      removeCustomTest(test.id);
                    }}
                    className="px-2 text-gray-500 hover:text-red-600 rounded"
                    title="Delete test"
                  >
                    ×
                  </button>
                </div>
              ))}
            </TabsList>

            {validationId && (
              <Button
                variant="outline"
                onClick={addCustomTest}
                className="ml-2 mt-2"
              >
                + New Test
              </Button>
            )}

            <div className="mt-4">
              <TabsContent value="main">
                {showLoadDialog && (
                  <div className="mb-4">
                    <form onSubmit={handleLoadValidation} className="flex gap-2">
                      <input
                        type="text"
                        value={loadValidationId}
                        onChange={(e) => setLoadValidationId(e.target.value)}
                        placeholder="Enter validation ID"
                        className="flex-1 p-2 border rounded"
                      />
                      <Button type="submit" disabled={!loadValidationId || isCreating}>
                        Load
                      </Button>
                      <Button type="button" variant="outline" onClick={() => setShowLoadDialog(false)}>
                        Cancel
                      </Button>
                    </form>
                  </div>
                )}

                <form onSubmit={handleCreateValidation}>
                  <div className="space-y-4">
                    {/* Source Files Group */}
                    <div className="border rounded-lg p-4">
                      <h3 className="text-lg font-medium mb-2">Source Files</h3>
                      <div className="space-y-2">
                        <FileInput
                          label="Documentation"
                          id="documentation"
                          name="documentation"
                          tooltip="Documentation describing the model's purpose, requirements, and usage. This will be used to understand the model and generate appropriate tests."
                          value={fileNames.documentation}
                          onChange={handleFileChange}
                          disabled={validationId}
                        />

                        <FileInput
                          label="Training Script"
                          id="trainingScript"
                          name="trainingScript"
                          tooltip="Python script containing the model's training code. This will be analyzed to understand the model's implementation and validate its behavior."
                          value={fileNames.trainingScript}
                          onChange={handleFileChange}
                          disabled={validationId}
                        />
                      </div>
                    </div>

                    {/* Testing Resources Group */}
                    <div className="border rounded-lg p-4">
                      <h3 className="text-lg font-medium mb-2">Testing Resources</h3>
                      <div className="space-y-2">
                        <FileInput
                          label="Trained Model"
                          id="trainedModel"
                          name="trainedModel"
                          tooltip="The trained model file that will be used for testing. This should be the output of your training process."
                          value={fileNames.trainedModel}
                          onChange={handleFileChange}
                          disabled={validationId}
                        />

                        <FileInput
                          label="Training Dataset"
                          id="trainingDataset"
                          name="trainingDataset"
                          tooltip="The dataset used to train the model. This will be used to validate training reproducibility and data handling."
                          value={fileNames.trainingDataset}
                          onChange={handleFileChange}
                          disabled={validationId}
                        />

                        <FileInput
                          label="Test Dataset"
                          id="testDataset"
                          name="testDataset"
                          tooltip="The dataset that will be used for testing. This should be different from the training dataset to evaluate model performance on unseen data."
                          value={fileNames.testDataset}
                          onChange={handleFileChange}
                          disabled={validationId}
                        />
                      </div>
                    </div>

                    <Button type="submit" disabled={isCreating || validationId}>
                      {isCreating ? 'Creating...' : validationId ? 'Validation Created' : 'Create Validation'}
                    </Button>
                  </div>
                </form>

                {status && (
                  <Alert className="mt-4">
                    {status}
                  </Alert>
                )}

                {error && (
                  <Alert variant="destructive" className="mt-4">
                    {error}
                  </Alert>
                )}

                {validationId && (
                  <Card className="mt-4 p-4">
                    <h3 className="text-lg font-medium mb-2">Validation Created Successfully</h3>
                    <p className="mb-2">Validation ID: {validationId}</p>
                    <p>You can now create and execute tests using the tabs above.</p>
                  </Card>
                )}
              </TabsContent>

              {customTests.map(test => (
                <TabsContent key={test.id} value={`test-${test.id}`}>
                  {renderTestTab(test)}
                </TabsContent>
              ))}
            </div>
          </div>
        </Tabs>
      </div>

      <AlertDialog open={!!testToDelete} onOpenChange={() => setTestToDelete(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Test</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete this test? This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={confirmDelete}>Delete</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

export default FormComponent;