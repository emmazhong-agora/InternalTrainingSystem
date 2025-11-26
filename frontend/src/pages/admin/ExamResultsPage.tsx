import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { examAPI } from '../../services/api';
import { ExamAttemptDetail, ExamStatistics } from '../../types';

export default function ExamResultsPage() {
  const { id } = useParams();
  const [attempts, setAttempts] = useState<ExamAttemptDetail[]>([]);
  const [statistics, setStatistics] = useState<ExamStatistics | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedAttempt, setSelectedAttempt] = useState<ExamAttemptDetail | null>(null);

  useEffect(() => {
    loadData();
  }, [id]);

  const loadData = async () => {
    if (!id) return;
    try {
      setLoading(true);
      const [attemptsData, statsData] = await Promise.all([
        examAPI.listExamAttempts(parseInt(id)),
        examAPI.getExamStatistics(parseInt(id))
      ]);
      setAttempts(attemptsData.attempts);
      setStatistics(statsData);
    } catch (error) {
      console.error('Failed to load results:', error);
      alert('Failed to load results');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs}s`;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                {statistics?.exam_title || 'Exam Results'}
              </h1>
              <p className="mt-2 text-sm text-gray-600">
                View all exam attempts and statistics
              </p>
            </div>
            <Link
              to="/admin/exams"
              className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
            >
              Back to Exams
            </Link>
          </div>
        </div>

        {/* Statistics Cards */}
        {statistics && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div className="bg-white shadow rounded-lg p-6">
              <p className="text-sm text-gray-600 mb-1">Total Attempts</p>
              <p className="text-3xl font-bold text-blue-600">{statistics.total_attempts}</p>
            </div>
            <div className="bg-white shadow rounded-lg p-6">
              <p className="text-sm text-gray-600 mb-1">Average Score</p>
              <p className="text-3xl font-bold text-purple-600">
                {statistics.average_score?.toFixed(1) || 'N/A'}%
              </p>
            </div>
            <div className="bg-white shadow rounded-lg p-6">
              <p className="text-sm text-gray-600 mb-1">Pass Rate</p>
              <p className="text-3xl font-bold text-green-600">
                {statistics.pass_rate?.toFixed(1) || 'N/A'}%
              </p>
            </div>
            <div className="bg-white shadow rounded-lg p-6">
              <p className="text-sm text-gray-600 mb-1">Score Range</p>
              <p className="text-xl font-bold text-gray-700">
                {statistics.lowest_score?.toFixed(0) || 'N/A'} - {statistics.highest_score?.toFixed(0) || 'N/A'}
              </p>
            </div>
          </div>
        )}

        {/* Attempts Table */}
        <div className="bg-white shadow rounded-lg overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">All Attempts</h2>
          </div>

          {attempts.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-500">No attempts yet</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      User
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Score
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Result
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Time Spent
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Submitted
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {attempts.map((attempt) => (
                    <tr key={attempt.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">
                          {attempt.user_email}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">
                          {attempt.score_percentage?.toFixed(1)}%
                        </div>
                        <div className="text-xs text-gray-500">
                          {attempt.earned_points} / {attempt.total_points} pts
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                            attempt.passed
                              ? 'bg-green-100 text-green-800'
                              : 'bg-red-100 text-red-800'
                          }`}
                        >
                          {attempt.passed ? 'PASSED' : 'FAILED'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {attempt.time_spent_seconds
                          ? formatTime(attempt.time_spent_seconds)
                          : 'N/A'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {formatDate(attempt.submitted_at || attempt.created_at)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <button
                          onClick={() => setSelectedAttempt(attempt)}
                          className="text-blue-600 hover:text-blue-900"
                        >
                          View Details
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Attempt Detail Modal */}
      {selectedAttempt && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 overflow-y-auto">
          <div className="bg-white rounded-lg max-w-4xl w-full m-4 max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex justify-between items-center">
              <div>
                <h3 className="text-lg font-semibold">Attempt Details</h3>
                <p className="text-sm text-gray-600">{selectedAttempt.user_email}</p>
              </div>
              <button
                onClick={() => setSelectedAttempt(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            </div>

            <div className="p-6">
              {/* Summary */}
              <div className="grid grid-cols-2 gap-4 mb-6 p-4 bg-gray-50 rounded-lg">
                <div>
                  <p className="text-sm text-gray-600">Score</p>
                  <p className="text-2xl font-bold text-blue-600">
                    {selectedAttempt.score_percentage?.toFixed(1)}%
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Result</p>
                  <p
                    className={`text-2xl font-bold ${
                      selectedAttempt.passed ? 'text-green-600' : 'text-red-600'
                    }`}
                  >
                    {selectedAttempt.passed ? 'PASSED' : 'FAILED'}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Points</p>
                  <p className="text-lg font-medium">
                    {selectedAttempt.earned_points} / {selectedAttempt.total_points}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Time Spent</p>
                  <p className="text-lg font-medium">
                    {selectedAttempt.time_spent_seconds
                      ? formatTime(selectedAttempt.time_spent_seconds)
                      : 'N/A'}
                  </p>
                </div>
              </div>

              {/* Answers */}
              <div>
                <h4 className="text-md font-semibold mb-4">Answers</h4>
                <div className="space-y-4">
                  {selectedAttempt.answers.map((answer, index) => (
                    <div
                      key={answer.id}
                      className={`p-4 rounded-lg border-2 ${
                        answer.is_correct
                          ? 'border-green-200 bg-green-50'
                          : 'border-red-200 bg-red-50'
                      }`}
                    >
                      <div className="flex items-start justify-between mb-2">
                        <span className="font-medium text-gray-900">
                          Question {index + 1} ({answer.question.points} pts)
                        </span>
                        <div className="text-right">
                          <span
                            className={`text-sm font-medium ${
                              answer.is_correct ? 'text-green-600' : 'text-red-600'
                            }`}
                          >
                            {answer.is_correct ? '✓ Correct' : '✗ Incorrect'}
                          </span>
                          <div className="text-xs text-gray-600">
                            {answer.points_earned} / {answer.question.points} pts
                          </div>
                        </div>
                      </div>
                      <p className="text-gray-700 mb-2">{answer.question.question_text}</p>
                      <div className="text-sm space-y-1">
                        <p className="text-gray-600">
                          <span className="font-medium">Student Answer:</span>{' '}
                          {answer.answer_text || '(Not answered)'}
                        </p>
                        <p className="text-gray-600">
                          <span className="font-medium">Correct Answer:</span>{' '}
                          {answer.question.correct_answer}
                        </p>
                        {answer.question.explanation && (
                          <p className="text-gray-600 mt-2">
                            <span className="font-medium">Explanation:</span>{' '}
                            {answer.question.explanation}
                          </p>
                        )}
                        {answer.manually_graded && answer.grader_feedback && (
                          <p className="text-blue-600 mt-2">
                            <span className="font-medium">Grader Feedback:</span>{' '}
                            {answer.grader_feedback}
                          </p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
