import React, { useState, useEffect, useRef } from 'react';
import { chatAPI } from '../services/api';
import VoiceChat from './VoiceChat';
import type {
  ChatMessage,
  ChatSession,
  MessageRole,
  TranscriptChunk,
} from '../types';

interface ChatPanelProps {
  videoId: number;
  currentTimestamp?: number;  // Current playback position
  onTimestampClick?: (timestamp: number) => void;
  onQuizRequest?: () => void;  // Callback to request a quiz
}

export const ChatPanel: React.FC<ChatPanelProps> = ({
  videoId,
  currentTimestamp,
  onTimestampClick,
  onQuizRequest,
}) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<number | null>(null);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [referencedChunks, setReferencedChunks] = useState<TranscriptChunk[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [contextPrompt, setContextPrompt] = useState<string | null>(null);
  const [showVoiceChat, setShowVoiceChat] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Check if transcript is processed
  useEffect(() => {
    const checkTranscriptProcessed = async () => {
      try {
        const info = await chatAPI.getCollectionInfo(videoId);
        if (!info.exists || info.chunk_count === 0) {
          // Process transcript
          setIsProcessing(true);
          await chatAPI.processTranscript(videoId);
          setIsProcessing(false);
        }
      } catch (err) {
        console.error('Error checking/processing transcript:', err);
        setError('Failed to process transcript. Please try again later.');
        setIsProcessing(false);
      }
    };

    checkTranscriptProcessed();
  }, [videoId]);

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const question = inputMessage.trim();
    setInputMessage('');
    setIsLoading(true);
    setError(null);

    try {
      const response = await chatAPI.askQuestion({
        session_id: currentSessionId || undefined,
        video_id: videoId,
        question,
        current_timestamp: currentTimestamp,
      });

      // Update session ID if this is the first message
      if (!currentSessionId) {
        setCurrentSessionId(response.session_id);
      }

      // Add messages to the list
      setMessages((prev) => [
        ...prev,
        response.user_message,
        response.assistant_message,
      ]);

      // Store referenced chunks for the assistant message
      if (response.referenced_chunks) {
        setReferencedChunks(response.referenced_chunks);
      }

      // Store context prompt for smart suggestions
      if (response.context_prompt) {
        setContextPrompt(response.context_prompt);
      }
    } catch (err: any) {
      console.error('Error sending message:', err);
      setError(err.response?.data?.detail || 'Failed to send message');
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const formatTimestamp = (seconds: number): string => {
    const minutes = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  };

  const renderMessage = (message: ChatMessage) => {
    const isUser = message.role === 'user';

    return (
      <div
        key={message.id}
        className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}
      >
        <div
          className={`max-w-[85%] rounded-lg px-4 py-2 ${
            isUser
              ? 'bg-blue-600 text-white'
              : 'bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-gray-100'
          }`}
        >
          <div className="text-sm whitespace-pre-wrap">{message.content}</div>

          {/* Show transcript references for assistant messages */}
          {!isUser && message.transcript_references && (
            <div className="mt-2 pt-2 border-t border-gray-300 dark:border-gray-600">
              <div className="text-xs font-semibold mb-1">
                Referenced Transcript:
              </div>
              {(() => {
                try {
                  const refs = JSON.parse(message.transcript_references);
                  return refs.map((chunk: TranscriptChunk, idx: number) => (
                    <button
                      key={idx}
                      onClick={() =>
                        onTimestampClick && onTimestampClick(chunk.start_time)
                      }
                      className="block text-xs text-blue-400 hover:text-blue-300 underline mb-1"
                    >
                      {formatTimestamp(chunk.start_time)} -{' '}
                      {formatTimestamp(chunk.end_time)}
                    </button>
                  ));
                } catch {
                  return null;
                }
              })()}
            </div>
          )}

          {/* Confidence score */}
          {!isUser && message.confidence_score !== null && (
            <div className="mt-1 text-xs opacity-70">
              Confidence: {message.confidence_score}%
            </div>
          )}

          <div className="text-xs opacity-60 mt-1">
            {new Date(message.created_at).toLocaleTimeString()}
          </div>
        </div>
      </div>
    );
  };

  if (isProcessing) {
    return (
      <div className="flex flex-col h-full bg-white dark:bg-gray-800 p-4">
        <div className="flex items-center justify-center h-full">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600 dark:text-gray-400">
              Processing video transcript...
            </p>
            <p className="text-sm text-gray-500 dark:text-gray-500 mt-2">
              This may take a minute
            </p>
          </div>
        </div>
      </div>
    );
  }

  // Show voice chat modal if enabled
  if (showVoiceChat) {
    return (
      <div className="flex flex-col h-full bg-white dark:bg-gray-800">
        <VoiceChat
          videoId={videoId}
          currentTimestamp={currentTimestamp}
          onClose={() => setShowVoiceChat(false)}
        />
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-white dark:bg-gray-800">
      {/* Header */}
      <div className="border-b border-gray-200 dark:border-gray-700 p-4">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            AI Teaching Assistant
          </h2>
          <button
            onClick={() => setShowVoiceChat(true)}
            className="p-2 text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg transition-colors"
            title="Start voice chat"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
            </svg>
          </button>
        </div>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          Ask questions via text or voice
        </p>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4">
        {messages.length === 0 ? (
          <div className="text-center text-gray-500 dark:text-gray-400 mt-8">
            <svg
              className="w-16 h-16 mx-auto mb-4 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
              />
            </svg>
            <p className="text-sm">Start a conversation!</p>
            <p className="text-xs mt-2">
              Ask questions about the video content and I'll help explain.
            </p>
          </div>
        ) : (
          <>
            {messages.map((message) => renderMessage(message))}
            <div ref={messagesEndRef} />
          </>
        )}

        {isLoading && (
          <div className="flex justify-start mb-4">
            <div className="bg-gray-200 dark:bg-gray-700 rounded-lg px-4 py-2">
              <div className="flex space-x-2">
                <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce"></div>
                <div
                  className="w-2 h-2 bg-gray-500 rounded-full animate-bounce"
                  style={{ animationDelay: '0.1s' }}
                ></div>
                <div
                  className="w-2 h-2 bg-gray-500 rounded-full animate-bounce"
                  style={{ animationDelay: '0.2s' }}
                ></div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Error Display */}
      {error && (
        <div className="px-4 py-2 bg-red-50 dark:bg-red-900/20 border-t border-red-200 dark:border-red-800">
          <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
        </div>
      )}

      {/* Context Prompt & Quiz Button */}
      {(contextPrompt || onQuizRequest) && (
        <div className="px-4 py-3 bg-blue-50 dark:bg-blue-900/20 border-t border-blue-200 dark:border-blue-800">
          {contextPrompt && (
            <div className="text-sm text-blue-800 dark:text-blue-300 mb-2 flex items-start">
              <svg className="w-4 h-4 mr-2 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
              </svg>
              <span>{contextPrompt}</span>
            </div>
          )}
          {onQuizRequest && (
            <button
              onClick={onQuizRequest}
              className="w-full px-3 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 transition-colors flex items-center justify-center"
            >
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              Test Your Understanding
            </button>
          )}
        </div>
      )}

      {/* Input Area */}
      <div className="border-t border-gray-200 dark:border-gray-700 p-4">
        <div className="flex space-x-2">
          <textarea
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask a question about the video..."
            className="flex-1 resize-none border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
            rows={2}
            disabled={isLoading}
          />
          <button
            onClick={handleSendMessage}
            disabled={isLoading || !inputMessage.trim()}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isLoading ? (
              <svg
                className="animate-spin h-5 w-5"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                ></circle>
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                ></path>
              </svg>
            ) : (
              <svg
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
                />
              </svg>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
