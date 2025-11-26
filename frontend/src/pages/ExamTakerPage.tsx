import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { examAPI } from '../services/api';
import {
  ExamPublic,
  ExamQuestionPublic,
  ExamAnswerCreate,
  ExamAttemptDetail,
  QuestionType
} from '../types';

export default function ExamTakerPage() {
  const { id } = useParams();
  const [exam, setExam] = useState<ExamPublic | null>(null);
  const [loading, setLoading] = useState(true);
  const [started, setStarted] = useState(false);
  const [attemptId, setAttemptId] = useState<number | null>(null);
  const [userEmail, setUserEmail] = useState('');
  const [answers, setAnswers] = useState<{ [questionId: number]: string }>({});
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<ExamAttemptDetail | null>(null);
  const [timeLeft, setTimeLeft] = useState<number | null>(null);
  const [startTime, setStartTime] = useState<number | null>(null);

  useEffect(() => {
    loadExam();
  }, [id]);

  useEffect(() => {
    const timeLimitMinutes = exam?.time_limit_minutes;
    if (!started || !startTime || !timeLimitMinutes) {
      return;
    }

    const interval = setInterval(() => {
      const elapsed = Math.floor((Date.now() - startTime) / 1000);
      const limit = timeLimitMinutes * 60;
      const remaining = limit - elapsed;

      if (remaining <= 0) {
        handleSubmit();
      } else {
        setTimeLeft(remaining);
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [started, startTime, exam?.time_limit_minutes]);

  const loadExam = async () => {
    if (!id) return;
    try {
      setLoading(true);
      const examData = await examAPI.getPublicExam(parseInt(id));
      setExam(examData);
    } catch (error) {
      console.error('Failed to load exam:', error);
      alert('Failed to load exam. It may not be available or published.');
    } finally {
      setLoading(false);
    }
  };

  const handleStart = async () => {
    if (!userEmail.trim()) {
      alert('Please enter your email address');
      return;
    }

    if (!exam) return;

    try {
      const attempt = await examAPI.startAttempt({
        exam_id: exam.id,
        user_email: userEmail
      });
      setAttemptId(attempt.id);
      setStarted(true);
      setStartTime(Date.now());
    } catch (error) {
      console.error('Failed to start exam:', error);
      alert('Failed to start exam. Make sure your email is registered in the system and you haven\'t exceeded the maximum attempts.');
    }
  };

  const handleSubmit = async () => {
    if (!attemptId || !exam) return;

    // Check if all questions are answered
    const unanswered = exam.questions.filter(q => !answers[q.id]);
    if (unanswered.length > 0) {
      if (!confirm(`You have ${unanswered.length} unanswered question(s). Submit anyway?`)) {
        return;
      }
    }

    try {
      setSubmitting(true);
      const answerData: ExamAnswerCreate[] = exam.questions.map(q => ({
        question_id: q.id,
        answer_text: answers[q.id] || ''
      }));

      const resultData = await examAPI.submitAttempt(attemptId, { answers: answerData });
      setResult(resultData);
    } catch (error) {
      console.error('Failed to submit exam:', error);
      alert('Failed to submit exam');
    } finally {
      setSubmitting(false);
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!exam) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Exam Not Found</h2>
          <p className="text-gray-600">This exam is not available or has been removed.</p>
        </div>
      </div>
    );
  }

  if (result) {
    return (
      <div className="min-h-screen bg-gray-50 py-12">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-white shadow rounded-lg p-8">
            <div className="text-center mb-8">
              <h2 className="text-3xl font-bold text-gray-900 mb-2">Exam Complete!</h2>
              <p className="text-gray-600">{exam.title}</p>
            </div>

            <div className="border-t border-b border-gray-200 py-6 mb-6">
              <div className="grid grid-cols-2 gap-4 text-center">
                <div>
                  <p className="text-sm text-gray-600 mb-1">Your Score</p>
                  <p className="text-3xl font-bold text-blue-600">
                    {result.score_percentage?.toFixed(1)}%
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-600 mb-1">Result</p>
                  <p className={`text-3xl font-bold ${result.passed ? 'text-green-600' : 'text-red-600'}`}>
                    {result.passed ? 'PASSED' : 'FAILED'}
                  </p>
                </div>
              </div>
            </div>

            <div className="space-y-3 mb-8">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Points Earned:</span>
                <span className="font-medium">{result.earned_points} / {result.total_points}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Pass Threshold:</span>
                <span className="font-medium">{exam.pass_threshold_percentage}%</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Time Spent:</span>
                <span className="font-medium">
                  {result.time_spent_seconds ? formatTime(result.time_spent_seconds) : 'N/A'}
                </span>
              </div>
            </div>

            {result.answers && result.answers.length > 0 && (
              <div className="border-t border-gray-200 pt-6">
                <h3 className="text-lg font-semibold mb-4">Answer Details</h3>
                <div className="space-y-4">
                  {result.answers.map((answer, index) => (
                    <div
                      key={answer.id}
                      className={`p-4 rounded-lg border-2 ${
                        answer.is_correct ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'
                      }`}
                    >
                      <div className="flex items-start justify-between mb-2">
                        <span className="font-medium text-gray-900">Question {index + 1}</span>
                        <span className={`text-sm font-medium ${answer.is_correct ? 'text-green-600' : 'text-red-600'}`}>
                          {answer.is_correct ? '✓ Correct' : '✗ Incorrect'}
                        </span>
                      </div>
                      <p className="text-gray-700 text-sm mb-2">{answer.question.question_text}</p>
                      <div className="text-sm">
                        <p className="text-gray-600">
                          Your answer: <span className="font-medium">{answer.answer_text || 'Not answered'}</span>
                        </p>
                        {answer.question.explanation && (
                          <p className="text-gray-600 mt-1">
                            <span className="font-medium">Explanation:</span> {answer.question.explanation}
                          </p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  if (!started) {
    return (
      <div className="min-h-screen bg-gray-50 py-12">
        <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-white shadow rounded-lg p-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-4">{exam.title}</h1>
            {exam.description && (
              <p className="text-gray-600 mb-6">{exam.description}</p>
            )}

            <div className="border-t border-b border-gray-200 py-6 mb-6 space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-600">Questions:</span>
                <span className="font-medium">{exam.question_count}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Total Points:</span>
                <span className="font-medium">{exam.total_points}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Pass Threshold:</span>
                <span className="font-medium">{exam.pass_threshold_percentage}%</span>
              </div>
              {exam.time_limit_minutes && (
                <div className="flex justify-between">
                  <span className="text-gray-600">Time Limit:</span>
                  <span className="font-medium">{exam.time_limit_minutes} minutes</span>
                </div>
              )}
              {exam.max_attempts && (
                <div className="flex justify-between">
                  <span className="text-gray-600">Max Attempts:</span>
                  <span className="font-medium">{exam.max_attempts}</span>
                </div>
              )}
            </div>

            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Email Address *
              </label>
              <input
                type="email"
                value={userEmail}
                onChange={(e) => setUserEmail(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                placeholder="your.email@example.com"
              />
              <p className="mt-1 text-sm text-gray-500">
                Must match your registered account email
              </p>
            </div>

            <button
              onClick={handleStart}
              className="w-full px-6 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 font-medium"
            >
              Start Exam
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header with Timer */}
        <div className="bg-white shadow rounded-lg p-4 mb-6 sticky top-0 z-10">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-lg font-semibold text-gray-900">{exam.title}</h2>
              <p className="text-sm text-gray-600">
                {exam.question_count} questions • {exam.total_points} points
              </p>
            </div>
            {timeLeft !== null && (
              <div className="text-right">
                <p className="text-sm text-gray-600">Time Remaining</p>
                <p className={`text-2xl font-bold ${timeLeft < 300 ? 'text-red-600' : 'text-blue-600'}`}>
                  {formatTime(timeLeft)}
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Questions */}
        <div className="space-y-6">
          {exam.questions.map((question, index) => (
            <div key={question.id} className="bg-white shadow rounded-lg p-6">
              <div className="mb-4">
                <span className="text-sm font-medium text-gray-500">Question {index + 1}</span>
                <h3 className="text-lg font-medium text-gray-900 mt-1">
                  {question.question_text}
                </h3>
                <p className="text-sm text-gray-500 mt-1">{question.points} points</p>
              </div>

              {question.question_type === QuestionType.MULTIPLE_CHOICE && question.options && (
                <div className="space-y-2">
                  {question.options.map((option, optIdx) => (
                    <label
                      key={optIdx}
                      className="flex items-start p-3 border border-gray-300 rounded-md hover:bg-gray-50 cursor-pointer"
                    >
                      <input
                        type="radio"
                        name={`question-${question.id}`}
                        value={optIdx.toString()}
                        checked={answers[question.id] === optIdx.toString()}
                        onChange={(e) => setAnswers({ ...answers, [question.id]: e.target.value })}
                        className="mt-1 mr-3"
                      />
                      <span className="text-gray-700">{option}</span>
                    </label>
                  ))}
                </div>
              )}

              {question.question_type === QuestionType.TRUE_FALSE && (
                <div className="space-y-2">
                  <label className="flex items-center p-3 border border-gray-300 rounded-md hover:bg-gray-50 cursor-pointer">
                    <input
                      type="radio"
                      name={`question-${question.id}`}
                      value="true"
                      checked={answers[question.id] === 'true'}
                      onChange={(e) => setAnswers({ ...answers, [question.id]: e.target.value })}
                      className="mr-3"
                    />
                    <span className="text-gray-700">True</span>
                  </label>
                  <label className="flex items-center p-3 border border-gray-300 rounded-md hover:bg-gray-50 cursor-pointer">
                    <input
                      type="radio"
                      name={`question-${question.id}`}
                      value="false"
                      checked={answers[question.id] === 'false'}
                      onChange={(e) => setAnswers({ ...answers, [question.id]: e.target.value })}
                      className="mr-3"
                    />
                    <span className="text-gray-700">False</span>
                  </label>
                </div>
              )}

              {question.question_type === QuestionType.SHORT_ANSWER && (
                <textarea
                  value={answers[question.id] || ''}
                  onChange={(e) => setAnswers({ ...answers, [question.id]: e.target.value })}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Type your answer here..."
                />
              )}
            </div>
          ))}
        </div>

        {/* Submit Button */}
        <div className="mt-8 bg-white shadow rounded-lg p-6">
          <div className="flex justify-between items-center">
            <div>
              <p className="text-sm text-gray-600">
                Answered: {Object.keys(answers).length} / {exam.question_count}
              </p>
            </div>
            <button
              onClick={handleSubmit}
              disabled={submitting}
              className="px-8 py-3 bg-green-600 text-white rounded-md hover:bg-green-700 font-medium disabled:bg-gray-400"
            >
              {submitting ? 'Submitting...' : 'Submit Exam'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
