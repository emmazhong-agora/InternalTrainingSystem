import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { examAPI, videosAPI } from '../../services/api';
import {
  ExamCreate,
  ExamUpdate,
  ExamQuestionCreate,
  QuestionType,
  ExamStatus,
  Video,
  QuestionGenerationRequest
} from '../../types';

export default function ExamCreatorPage() {
  const navigate = useNavigate();
  const { id } = useParams();
  const isEditing = !!id;

  const [loading, setLoading] = useState(false);
  const [videos, setVideos] = useState<Video[]>([]);
  const [generatingQuestions, setGeneratingQuestions] = useState(false);

  // Exam fields
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [timeLimitMinutes, setTimeLimitMinutes] = useState<number | undefined>();
  const [passThreshold, setPassThreshold] = useState(70);
  const [maxAttempts, setMaxAttempts] = useState<number | undefined>();
  const [status, setStatus] = useState<ExamStatus>(ExamStatus.DRAFT);
  const [showCorrectAnswers, setShowCorrectAnswers] = useState(false);
  const [selectedVideoIds, setSelectedVideoIds] = useState<number[]>([]);

  // Questions
  const [questions, setQuestions] = useState<ExamQuestionCreate[]>([]);

  // AI Generation
  const [showAIDialog, setShowAIDialog] = useState(false);
  const [aiVideoIds, setAiVideoIds] = useState<number[]>([]);
  const [aiNumQuestions, setAiNumQuestions] = useState(5);
  const [aiDifficulty, setAiDifficulty] = useState('medium');

  useEffect(() => {
    loadVideos();
    if (isEditing) {
      loadExam();
    }
  }, [id]);

  const loadVideos = async () => {
    try {
      const response = await videosAPI.list({ page_size: 100 });
      setVideos(response.videos);
    } catch (error) {
      console.error('Failed to load videos:', error);
    }
  };

  const loadExam = async () => {
    if (!id) return;
    try {
      setLoading(true);
      const exam = await examAPI.getExam(parseInt(id));
      setTitle(exam.title);
      setDescription(exam.description || '');
      setTimeLimitMinutes(exam.time_limit_minutes);
      setPassThreshold(exam.pass_threshold_percentage);
      setMaxAttempts(exam.max_attempts);
      setStatus(exam.status);
      setShowCorrectAnswers(exam.show_correct_answers);
      setSelectedVideoIds(exam.video_ids);
      setQuestions(exam.questions.map(q => ({
        question_type: q.question_type,
        question_text: q.question_text,
        points: q.points,
        options: q.options,
        correct_answer: q.correct_answer,
        explanation: q.explanation,
        sort_order: q.sort_order,
        source_video_id: q.source_video_id
      })));
    } catch (error) {
      console.error('Failed to load exam:', error);
      alert('Failed to load exam');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!title.trim()) {
      alert('Please enter an exam title');
      return;
    }

    try {
      setLoading(true);

      if (isEditing) {
        // Update exam
        const updateData: ExamUpdate = {
          title,
          description,
          time_limit_minutes: timeLimitMinutes,
          pass_threshold_percentage: passThreshold,
          max_attempts: maxAttempts,
          status,
          show_correct_answers: showCorrectAnswers
        };
        await examAPI.updateExam(parseInt(id!), updateData);

        // Note: In a full implementation, you'd also handle updating questions
        // For now, questions are added separately
      } else {
        // Create exam
        const createData: ExamCreate = {
          title,
          description,
          time_limit_minutes: timeLimitMinutes,
          pass_threshold_percentage: passThreshold,
          max_attempts: maxAttempts,
          status,
          show_correct_answers: showCorrectAnswers,
          video_ids: selectedVideoIds
        };
        const exam = await examAPI.createExam(createData);

        // Add questions
        if (questions.length > 0) {
          await examAPI.addGeneratedQuestions(exam.id, questions);
        }

        navigate(`/admin/exams/${exam.id}/edit`);
      }

      alert('Exam saved successfully!');
    } catch (error) {
      console.error('Failed to save exam:', error);
      alert('Failed to save exam');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateQuestions = async () => {
    if (aiVideoIds.length === 0) {
      alert('Please select at least one video');
      return;
    }

    try {
      setGeneratingQuestions(true);
      const request: QuestionGenerationRequest = {
        video_ids: aiVideoIds,
        num_questions: aiNumQuestions,
        difficulty: aiDifficulty,
        question_types: [QuestionType.MULTIPLE_CHOICE, QuestionType.TRUE_FALSE]
      };

      const response = await examAPI.generateQuestions(request);

      // Add generated questions to the list
      const newQuestions: ExamQuestionCreate[] = response.questions.map((q, index) => ({
        question_type: q.question_type,
        question_text: q.question_text,
        points: 1.0,
        options: q.options,
        correct_answer: q.correct_answer,
        explanation: q.explanation,
        sort_order: questions.length + index,
        source_video_id: q.source_video_id
      }));

      setQuestions([...questions, ...newQuestions]);
      setShowAIDialog(false);
      alert(`Generated ${response.total_generated} questions!`);
    } catch (error) {
      console.error('Failed to generate questions:', error);
      alert('Failed to generate questions');
    } finally {
      setGeneratingQuestions(false);
    }
  };

  const addQuestion = () => {
    setQuestions([
      ...questions,
      {
        question_type: QuestionType.MULTIPLE_CHOICE,
        question_text: '',
        points: 1.0,
        options: ['', '', '', ''],
        correct_answer: '0',
        sort_order: questions.length
      }
    ]);
  };

  const removeQuestion = (index: number) => {
    setQuestions(questions.filter((_, i) => i !== index));
  };

  const updateQuestion = (index: number, field: keyof ExamQuestionCreate, value: any) => {
    const updated = [...questions];
    updated[index] = { ...updated[index], [field]: value };
    setQuestions(updated);
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
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">
            {isEditing ? 'Edit Exam' : 'Create New Exam'}
          </h1>
          <p className="mt-2 text-sm text-gray-600">
            Create an exam with questions or use AI to generate them from videos
          </p>
        </div>

        {/* Exam Details */}
        <div className="bg-white shadow rounded-lg p-6 mb-6">
          <h2 className="text-lg font-semibold mb-4">Exam Details</h2>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Title *
              </label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                placeholder="e.g., Python Basics Assessment"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Description
              </label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                placeholder="Brief description of the exam"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Time Limit (minutes)
                </label>
                <input
                  type="number"
                  value={timeLimitMinutes ?? ''}
                  onChange={(e) => {
                    const val = e.target.value;
                    setTimeLimitMinutes(val ? parseInt(val, 10) : undefined);
                  }}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  placeholder="No limit"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Pass Threshold (%)
                </label>
                <input
                  type="number"
                  value={passThreshold.toString()}
                  onChange={(e) => {
                    const val = e.target.value ? parseInt(e.target.value, 10) : 70;
                    if (!isNaN(val)) setPassThreshold(val);
                  }}
                  min="0"
                  max="100"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Max Attempts
                </label>
                <input
                  type="number"
                  value={maxAttempts ?? ''}
                  onChange={(e) => {
                    const val = e.target.value;
                    setMaxAttempts(val ? parseInt(val, 10) : undefined);
                  }}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Unlimited"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Status
                </label>
                <select
                  value={status}
                  onChange={(e) => setStatus(e.target.value as ExamStatus)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value={ExamStatus.DRAFT}>Draft</option>
                  <option value={ExamStatus.PUBLISHED}>Published</option>
                  <option value={ExamStatus.ARCHIVED}>Archived</option>
                </select>
              </div>
            </div>

            <div className="flex items-center">
              <input
                type="checkbox"
                checked={showCorrectAnswers}
                onChange={(e) => setShowCorrectAnswers(e.target.checked)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label className="ml-2 block text-sm text-gray-700">
                Show correct answers after submission
              </label>
            </div>
          </div>
        </div>

        {/* Questions Section */}
        <div className="bg-white shadow rounded-lg p-6 mb-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold">Questions ({questions.length})</h2>
            <div className="space-x-2">
              <button
                onClick={() => setShowAIDialog(true)}
                className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700"
              >
                Generate with AI
              </button>
              <button
                onClick={addQuestion}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Add Question
              </button>
            </div>
          </div>

          {questions.length === 0 ? (
            <p className="text-gray-500 text-center py-8">
              No questions yet. Add manually or generate with AI.
            </p>
          ) : (
            <div className="space-y-4">
              {questions.map((question, index) => (
                <div key={index} className="border border-gray-300 rounded-lg p-4">
                  <div className="flex justify-between items-start mb-3">
                    <span className="text-sm font-medium text-gray-700">Question {index + 1}</span>
                    <button
                      onClick={() => removeQuestion(index)}
                      className="text-red-600 hover:text-red-800 text-sm"
                    >
                      Remove
                    </button>
                  </div>

                  <div className="space-y-3">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Question Type
                      </label>
                      <select
                        value={question.question_type}
                        onChange={(e) => updateQuestion(index, 'question_type', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md"
                      >
                        <option value={QuestionType.MULTIPLE_CHOICE}>Multiple Choice</option>
                        <option value={QuestionType.TRUE_FALSE}>True/False</option>
                        <option value={QuestionType.SHORT_ANSWER}>Short Answer</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Question Text
                      </label>
                      <textarea
                        value={question.question_text}
                        onChange={(e) => updateQuestion(index, 'question_text', e.target.value)}
                        rows={2}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md"
                      />
                    </div>

                    {question.question_type === QuestionType.MULTIPLE_CHOICE && (
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Options
                        </label>
                        {(question.options || ['', '', '', '']).map((option, optIdx) => (
                          <div key={optIdx} className="flex items-center mb-2">
                            <input
                              type="radio"
                              name={`correct-${index}`}
                              checked={question.correct_answer === optIdx.toString()}
                              onChange={() => updateQuestion(index, 'correct_answer', optIdx.toString())}
                              className="mr-2"
                            />
                            <input
                              type="text"
                              value={option}
                              onChange={(e) => {
                                const newOptions = [...(question.options || [])];
                                newOptions[optIdx] = e.target.value;
                                updateQuestion(index, 'options', newOptions);
                              }}
                              className="flex-1 px-3 py-2 border border-gray-300 rounded-md"
                              placeholder={`Option ${optIdx + 1}`}
                            />
                          </div>
                        ))}
                      </div>
                    )}

                    {question.question_type === QuestionType.TRUE_FALSE && (
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Correct Answer
                        </label>
                        <select
                          value={question.correct_answer}
                          onChange={(e) => updateQuestion(index, 'correct_answer', e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md"
                        >
                          <option value="true">True</option>
                          <option value="false">False</option>
                        </select>
                      </div>
                    )}

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Points
                        </label>
                        <input
                          type="number"
                          value={question.points?.toString() ?? '1'}
                          onChange={(e) => {
                            const val = e.target.value ? parseFloat(e.target.value) : 1;
                            if (!isNaN(val)) updateQuestion(index, 'points', val);
                          }}
                          step="0.5"
                          min="0"
                          className="w-full px-3 py-2 border border-gray-300 rounded-md"
                        />
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex justify-between">
          <button
            onClick={() => navigate('/admin/exams')}
            className="px-6 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={loading}
            className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400"
          >
            {loading ? 'Saving...' : 'Save Exam'}
          </button>
        </div>
      </div>

      {/* AI Generation Dialog */}
      {showAIDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full">
            <h3 className="text-lg font-semibold mb-4">Generate Questions with AI</h3>

            <div className="space-y-4 mb-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Select Videos
                </label>
                <div className="max-h-48 overflow-y-auto border border-gray-300 rounded-md p-2">
                  {videos.map((video) => (
                    <div key={video.id} className="flex items-center mb-2">
                      <input
                        type="checkbox"
                        checked={aiVideoIds.includes(video.id)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setAiVideoIds([...aiVideoIds, video.id]);
                          } else {
                            setAiVideoIds(aiVideoIds.filter(id => id !== video.id));
                          }
                        }}
                        className="mr-2"
                      />
                      <span className="text-sm">{video.title}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Number of Questions
                </label>
                <input
                  type="number"
                  value={aiNumQuestions.toString()}
                  onChange={(e) => {
                    const val = e.target.value ? parseInt(e.target.value, 10) : 5;
                    if (!isNaN(val) && val >= 1 && val <= 50) setAiNumQuestions(val);
                  }}
                  min="1"
                  max="50"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Difficulty
                </label>
                <select
                  value={aiDifficulty}
                  onChange={(e) => setAiDifficulty(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                >
                  <option value="easy">Easy</option>
                  <option value="medium">Medium</option>
                  <option value="hard">Hard</option>
                </select>
              </div>
            </div>

            <div className="flex justify-end space-x-2">
              <button
                onClick={() => setShowAIDialog(false)}
                className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleGenerateQuestions}
                disabled={generatingQuestions || aiVideoIds.length === 0}
                className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:bg-gray-400"
              >
                {generatingQuestions ? 'Generating...' : 'Generate'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
