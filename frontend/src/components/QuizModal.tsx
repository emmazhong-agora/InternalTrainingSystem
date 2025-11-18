import React, { useState, useEffect } from 'react';
import { chatAPI } from '../services/api';
import type { QuizQuestion } from '../types';

interface QuizModalProps {
  videoId: number;
  currentTimestamp?: number;
  isOpen: boolean;
  onClose: () => void;
}

export const QuizModal: React.FC<QuizModalProps> = ({
  videoId,
  currentTimestamp,
  isOpen,
  onClose,
}) => {
  const [quiz, setQuiz] = useState<QuizQuestion | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedAnswer, setSelectedAnswer] = useState<number | null>(null);
  const [showResult, setShowResult] = useState(false);

  useEffect(() => {
    if (isOpen) {
      generateQuiz();
    }
  }, [isOpen, videoId]);

  const generateQuiz = async () => {
    setLoading(true);
    setError(null);
    setSelectedAnswer(null);
    setShowResult(false);

    try {
      const response = await chatAPI.generateQuiz({
        video_id: videoId,
        current_timestamp: currentTimestamp,
        difficulty: 'medium',
      });

      setQuiz(response.quiz);
    } catch (err: any) {
      console.error('Error generating quiz:', err);
      setError(err.response?.data?.detail || 'Failed to generate quiz');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = () => {
    if (selectedAnswer !== null) {
      setShowResult(true);
    }
  };

  const handleReset = () => {
    generateQuiz();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center">
            <svg className="w-6 h-6 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
            Quiz Time!
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {loading && (
            <div className="flex flex-col items-center justify-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
              <p className="text-gray-600 dark:text-gray-400">Generating quiz question...</p>
            </div>
          )}

          {error && (
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
              <p className="text-red-600 dark:text-red-400">{error}</p>
              <button
                onClick={generateQuiz}
                className="mt-3 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
              >
                Try Again
              </button>
            </div>
          )}

          {quiz && !loading && (
            <div className="space-y-6">
              {/* Question */}
              <div>
                <p className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                  {quiz.question}
                </p>
              </div>

              {/* Options */}
              <div className="space-y-3">
                {quiz.options.map((option, index) => {
                  const isSelected = selectedAnswer === index;
                  const isCorrect = index === quiz.correct_answer;
                  const showCorrect = showResult && isCorrect;
                  const showIncorrect = showResult && isSelected && !isCorrect;

                  return (
                    <button
                      key={index}
                      onClick={() => !showResult && setSelectedAnswer(index)}
                      disabled={showResult}
                      className={`w-full text-left p-4 rounded-lg border-2 transition-all ${
                        showCorrect
                          ? 'border-green-500 bg-green-50 dark:bg-green-900/20'
                          : showIncorrect
                          ? 'border-red-500 bg-red-50 dark:bg-red-900/20'
                          : isSelected
                          ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                          : 'border-gray-300 dark:border-gray-600 hover:border-blue-400 dark:hover:border-blue-500'
                      } ${
                        showResult ? 'cursor-default' : 'cursor-pointer'
                      }`}
                    >
                      <div className="flex items-center">
                        <span
                          className={`w-6 h-6 rounded-full border-2 flex items-center justify-center mr-3 ${
                            showCorrect
                              ? 'border-green-500 bg-green-500'
                              : showIncorrect
                              ? 'border-red-500 bg-red-500'
                              : isSelected
                              ? 'border-blue-500 bg-blue-500'
                              : 'border-gray-400'
                          }`}
                        >
                          {showCorrect && (
                            <svg
                              className="w-4 h-4 text-white"
                              fill="none"
                              stroke="currentColor"
                              viewBox="0 0 24 24"
                            >
                              <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M5 13l4 4L19 7"
                              />
                            </svg>
                          )}
                          {showIncorrect && (
                            <svg
                              className="w-4 h-4 text-white"
                              fill="none"
                              stroke="currentColor"
                              viewBox="0 0 24 24"
                            >
                              <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M6 18L18 6M6 6l12 12"
                              />
                            </svg>
                          )}
                          {isSelected && !showResult && (
                            <div className="w-2 h-2 bg-white rounded-full"></div>
                          )}
                        </span>
                        <span className="text-gray-900 dark:text-white">{option}</span>
                      </div>
                    </button>
                  );
                })}
              </div>

              {/* Explanation */}
              {showResult && (
                <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
                  <h3 className="font-semibold text-blue-900 dark:text-blue-300 mb-2">
                    Explanation:
                  </h3>
                  <p className="text-blue-800 dark:text-blue-200">{quiz.explanation}</p>
                </div>
              )}

              {/* Result Message */}
              {showResult && (
                <div
                  className={`text-center p-4 rounded-lg ${
                    selectedAnswer === quiz.correct_answer
                      ? 'bg-green-50 dark:bg-green-900/20 text-green-800 dark:text-green-300'
                      : 'bg-red-50 dark:bg-red-900/20 text-red-800 dark:text-red-300'
                  }`}
                >
                  <p className="text-lg font-semibold">
                    {selectedAnswer === quiz.correct_answer
                      ? '🎉 Correct! Great job!'
                      : '❌ Not quite. Review the explanation above.'}
                  </p>
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex gap-3">
                {!showResult ? (
                  <button
                    onClick={handleSubmit}
                    disabled={selectedAnswer === null}
                    className="flex-1 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
                  >
                    Submit Answer
                  </button>
                ) : (
                  <>
                    <button
                      onClick={handleReset}
                      className="flex-1 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
                    >
                      Try Another Question
                    </button>
                    <button
                      onClick={onClose}
                      className="flex-1 px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors font-medium"
                    >
                      Close
                    </button>
                  </>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
