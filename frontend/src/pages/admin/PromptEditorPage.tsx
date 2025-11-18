import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { promptsAPI } from '../../services/api';
import type { PromptTemplate, PromptTemplateCreate, PromptTemplateUpdate } from '../../types';

const PromptEditorPage: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const isEditMode = !!id;

  const [loading, setLoading] = useState(isEditMode);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form data
  const [formData, setFormData] = useState<PromptTemplateCreate>({
    name: '',
    category: 'chat',
    description: '',
    system_message: '',
    user_message_template: '',
    model: 'gpt-4o',
    temperature: 0.7,
    max_tokens: 1000,
    top_p: 1.0,
    variables: [],
    response_format: 'text',
    response_schema: null,
    version: '1.0',
    is_active: true,
    is_default: false,
  });

  // Preview state
  const [showPreview, setShowPreview] = useState(false);
  const [previewVariables, setPreviewVariables] = useState<{ [key: string]: string }>({});
  const [renderedPreview, setRenderedPreview] = useState<string>('');

  useEffect(() => {
    if (isEditMode && id) {
      loadPrompt(parseInt(id));
    }
  }, [id]);

  // Extract variables from template
  useEffect(() => {
    const extractVariables = (text: string): string[] => {
      const regex = /\{([^}]+)\}/g;
      const matches = text.match(regex);
      if (!matches) return [];
      return [...new Set(matches.map(m => m.slice(1, -1)))];
    };

    const systemVars = extractVariables(formData.system_message);
    const userVars = formData.user_message_template
      ? extractVariables(formData.user_message_template)
      : [];
    const allVars = [...new Set([...systemVars, ...userVars])];

    setFormData(prev => ({ ...prev, variables: allVars }));

    // Initialize preview variables
    const newPreviewVars: { [key: string]: string } = {};
    allVars.forEach(v => {
      if (!previewVariables[v]) {
        newPreviewVars[v] = `sample_${v}`;
      } else {
        newPreviewVars[v] = previewVariables[v];
      }
    });
    setPreviewVariables(newPreviewVars);
  }, [formData.system_message, formData.user_message_template]);

  // Render preview with variables
  useEffect(() => {
    if (showPreview) {
      let preview = formData.system_message;
      Object.entries(previewVariables).forEach(([key, value]) => {
        preview = preview.replace(new RegExp(`\\{${key}\\}`, 'g'), value || `{${key}}`);
      });
      setRenderedPreview(preview);
    }
  }, [showPreview, formData.system_message, previewVariables]);

  const loadPrompt = async (promptId: number) => {
    try {
      setLoading(true);
      setError(null);
      const prompt = await promptsAPI.getById(promptId);

      setFormData({
        name: prompt.name,
        category: prompt.category,
        description: prompt.description || '',
        system_message: prompt.system_message,
        user_message_template: prompt.user_message_template || '',
        model: prompt.model,
        temperature: prompt.temperature,
        max_tokens: prompt.max_tokens,
        top_p: prompt.top_p || 1.0,
        variables: prompt.variables || [],
        response_format: prompt.response_format || 'text',
        response_schema: prompt.response_schema,
        version: prompt.version,
        is_active: prompt.is_active,
        is_default: prompt.is_default,
      });
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load prompt');
      console.error('Error loading prompt:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      setSaving(true);
      setError(null);

      if (isEditMode && id) {
        await promptsAPI.update(parseInt(id), formData as PromptTemplateUpdate);
      } else {
        await promptsAPI.create(formData);
      }

      navigate('/admin/prompts');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save prompt');
      console.error('Error saving prompt:', err);
    } finally {
      setSaving(false);
    }
  };

  const handleChange = (field: keyof PromptTemplateCreate, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-gray-300 border-t-indigo-600"></div>
          <p className="mt-2 text-gray-600">Loading prompt...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <button
            onClick={() => navigate('/admin/prompts')}
            className="text-indigo-600 hover:text-indigo-800 mb-4 inline-flex items-center"
          >
            ← Back to Prompts
          </button>
          <h1 className="text-3xl font-bold text-gray-900">
            {isEditMode ? 'Edit Prompt' : 'Create New Prompt'}
          </h1>
          <p className="mt-2 text-sm text-gray-600">
            {isEditMode
              ? 'Update prompt configuration and content'
              : 'Create a new prompt template for AI services'}
          </p>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-800">{error}</p>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Basic Information */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Basic Information</h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Name *
                </label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => handleChange('name', e.target.value)}
                  placeholder="e.g., chat_qa_main"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Category *
                </label>
                <select
                  required
                  value={formData.category}
                  onChange={(e) => handleChange('category', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="chat">Chat</option>
                  <option value="quiz">Quiz</option>
                  <option value="voice_ai">Voice AI</option>
                  <option value="analysis">Analysis</option>
                </select>
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) => handleChange('description', e.target.value)}
                  placeholder="Brief description of this prompt's purpose"
                  rows={2}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>
            </div>
          </div>

          {/* Prompt Content */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Prompt Content</h2>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  System Message *
                </label>
                <p className="text-xs text-gray-500 mb-2">
                  Use &#123;variable_name&#125; for dynamic content
                </p>
                <textarea
                  required
                  value={formData.system_message}
                  onChange={(e) => handleChange('system_message', e.target.value)}
                  placeholder="You are an AI assistant..."
                  rows={6}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 font-mono text-sm"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  User Message Template
                </label>
                <p className="text-xs text-gray-500 mb-2">
                  Optional template for user message with variables
                </p>
                <textarea
                  value={formData.user_message_template}
                  onChange={(e) => handleChange('user_message_template', e.target.value)}
                  placeholder="Video content at {timestamp}s..."
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 font-mono text-sm"
                />
              </div>

              {/* Detected Variables */}
              {formData.variables && formData.variables.length > 0 && (
                <div className="bg-blue-50 border border-blue-200 rounded-md p-3">
                  <p className="text-sm font-medium text-blue-900 mb-2">
                    Detected Variables:
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {formData.variables.map((v) => (
                      <span
                        key={v}
                        className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs font-mono"
                      >
                        &#123;{v}&#125;
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Model Configuration */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Model Configuration</h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Model *
                </label>
                <select
                  required
                  value={formData.model}
                  onChange={(e) => handleChange('model', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="gpt-4o">GPT-4o</option>
                  <option value="gpt-4o-mini">GPT-4o Mini</option>
                  <option value="gpt-4-turbo">GPT-4 Turbo</option>
                  <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Temperature (0-2)
                </label>
                <input
                  type="number"
                  step="0.1"
                  min="0"
                  max="2"
                  value={formData.temperature}
                  onChange={(e) => handleChange('temperature', parseFloat(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Max Tokens
                </label>
                <input
                  type="number"
                  min="1"
                  value={formData.max_tokens}
                  onChange={(e) => handleChange('max_tokens', parseInt(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Top P (0-1)
                </label>
                <input
                  type="number"
                  step="0.1"
                  min="0"
                  max="1"
                  value={formData.top_p}
                  onChange={(e) => handleChange('top_p', parseFloat(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Response Format
                </label>
                <select
                  value={formData.response_format}
                  onChange={(e) => handleChange('response_format', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="text">Text</option>
                  <option value="json">JSON</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Version
                </label>
                <input
                  type="text"
                  value={formData.version}
                  onChange={(e) => handleChange('version', e.target.value)}
                  placeholder="1.0"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>
            </div>
          </div>

          {/* Status & Flags */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Status & Settings</h2>

            <div className="space-y-3">
              <label className="flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.is_active}
                  onChange={(e) => handleChange('is_active', e.target.checked)}
                  className="w-4 h-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
                />
                <span className="ml-2 text-sm text-gray-700">
                  <strong>Active:</strong> Prompt is available for use
                </span>
              </label>

              <label className="flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.is_default}
                  onChange={(e) => handleChange('is_default', e.target.checked)}
                  className="w-4 h-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
                />
                <span className="ml-2 text-sm text-gray-700">
                  <strong>Default:</strong> Use as default prompt for this category
                </span>
              </label>
            </div>
          </div>

          {/* Preview Section */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold text-gray-900">Preview</h2>
              <button
                type="button"
                onClick={() => setShowPreview(!showPreview)}
                className="px-4 py-2 bg-indigo-100 text-indigo-700 rounded-md hover:bg-indigo-200 transition-colors"
              >
                {showPreview ? 'Hide Preview' : 'Show Preview'}
              </button>
            </div>

            {showPreview && (
              <div className="space-y-4">
                {/* Variable Inputs */}
                {formData.variables && formData.variables.length > 0 && (
                  <div>
                    <p className="text-sm font-medium text-gray-700 mb-2">
                      Test Variables:
                    </p>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {formData.variables.map((v) => (
                        <div key={v}>
                          <label className="block text-xs text-gray-600 mb-1">
                            &#123;{v}&#125;
                          </label>
                          <input
                            type="text"
                            value={previewVariables[v] || ''}
                            onChange={(e) =>
                              setPreviewVariables(prev => ({ ...prev, [v]: e.target.value }))
                            }
                            placeholder={`Enter ${v}`}
                            className="w-full px-2 py-1 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                          />
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Rendered Preview */}
                <div>
                  <p className="text-sm font-medium text-gray-700 mb-2">
                    Rendered System Message:
                  </p>
                  <div className="bg-gray-50 border border-gray-200 rounded-md p-4">
                    <pre className="whitespace-pre-wrap text-sm font-mono text-gray-800">
                      {renderedPreview || 'No system message'}
                    </pre>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-4">
            <button
              type="button"
              onClick={() => navigate('/admin/prompts')}
              className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving}
              className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {saving ? 'Saving...' : isEditMode ? 'Update Prompt' : 'Create Prompt'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default PromptEditorPage;
