import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { examAPI } from '../../services/api';
import { Exam, ExamStatus } from '../../types';

export default function ExamsListPage() {
  const navigate = useNavigate();
  const [exams, setExams] = useState<Exam[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('');

  useEffect(() => {
    loadExams();
  }, [searchQuery, statusFilter]);

  const loadExams = async () => {
    try {
      setLoading(true);
      const response = await examAPI.listExams({
        search: searchQuery || undefined,
        status_filter: statusFilter || undefined,
      });
      setExams(response.exams);
    } catch (error) {
      console.error('Failed to load exams:', error);
      alert('Failed to load exams');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (examId: number) => {
    if (!confirm('Are you sure you want to delete this exam?')) return;

    try {
      await examAPI.deleteExam(examId);
      alert('Exam deleted successfully');
      loadExams();
    } catch (error) {
      console.error('Failed to delete exam:', error);
      alert('Failed to delete exam');
    }
  };

  const getStatusBadgeColor = (status: ExamStatus) => {
    switch (status) {
      case ExamStatus.PUBLISHED:
        return 'bg-green-100 text-green-800';
      case ExamStatus.DRAFT:
        return 'bg-gray-100 text-gray-800';
      case ExamStatus.ARCHIVED:
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Exam Management</h1>
              <p className="mt-2 text-sm text-gray-600">
                Create and manage exams for training assessments
              </p>
            </div>
            <button
              onClick={() => navigate('/admin/exams/create')}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              Create New Exam
            </button>
          </div>
        </div>

        {/* Filters */}
        <div className="mb-6 grid grid-cols-1 md:grid-cols-2 gap-4">
          <input
            type="text"
            placeholder="Search exams..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
          />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="">All Status</option>
            <option value="draft">Draft</option>
            <option value="published">Published</option>
            <option value="archived">Archived</option>
          </select>
        </div>

        {/* Exams List */}
        {loading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          </div>
        ) : exams.length === 0 ? (
          <div className="text-center py-12 bg-white rounded-lg shadow">
            <p className="text-gray-500">No exams found. Create your first exam to get started!</p>
          </div>
        ) : (
          <div className="bg-white shadow rounded-lg overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Title
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Questions
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Pass Rate
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {exams.map((exam) => (
                  <tr key={exam.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <div className="text-sm font-medium text-gray-900">{exam.title}</div>
                        {exam.description && (
                          <div className="text-sm text-gray-500 truncate max-w-xs">
                            {exam.description}
                          </div>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusBadgeColor(exam.status)}`}>
                        {exam.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {exam.question_count} questions ({exam.total_points} pts)
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {exam.pass_threshold_percentage}%
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                      <Link
                        to={`/admin/exams/${exam.id}/edit`}
                        className="text-blue-600 hover:text-blue-900"
                      >
                        Edit
                      </Link>
                      <Link
                        to={`/admin/exams/${exam.id}/results`}
                        className="text-green-600 hover:text-green-900"
                      >
                        Results
                      </Link>
                      {exam.status === ExamStatus.PUBLISHED && (
                        <button
                          onClick={() => {
                            const url = `${window.location.origin}/exam/${exam.id}`;
                            navigator.clipboard.writeText(url);
                            alert('Exam URL copied to clipboard!');
                          }}
                          className="text-purple-600 hover:text-purple-900"
                        >
                          Copy URL
                        </button>
                      )}
                      <button
                        onClick={() => handleDelete(exam.id)}
                        className="text-red-600 hover:text-red-900"
                      >
                        Delete
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
  );
}
