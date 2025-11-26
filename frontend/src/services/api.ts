import axios from 'axios';
import type {
  AuthResponse,
  LoginCredentials,
  RegisterData,
  VideoListResponse,
  Video,
  VideoCategory,
  LearningProgress,
  ProgressUpdate,
  VideoUploadData,
  Material,
  MaterialUploadData,
  MaterialListResponse,
  AskQuestionRequest,
  AskQuestionResponse,
  ChatSession,
  ChatSessionListResponse,
  GenerateQuizRequest,
  GenerateQuizResponse,
  GenerateTokenRequest,
  GenerateTokenResponse,
  InviteAgentRequest,
  InviteAgentResponse,
  StopConversationRequest,
  PromptTemplate,
  PromptTemplateCreate,
  PromptTemplateUpdate,
  PromptTemplateListResponse,
  PromptRenderRequest,
  PromptRenderResponse,
  UserDetailResponse,
  UserListResponse,
  UserCreateData,
  UserUpdateData,
  VideoCategoryTree,
  VideoCategoryCreate,
  VideoCategoryUpdate,
  SystemOverview,
  UserStatistics,
  VideoStatistics,
  CategoryStatistics,
  PopularContent,
  Exam,
  ExamCreate,
  ExamUpdate,
  ExamListResponse,
  ExamPublic,
  ExamQuestionCreate,
  ExamQuestionUpdate,
  ExamQuestion,
  ExamAttemptCreate,
  ExamAttempt,
  ExamAttemptSubmit,
  ExamAttemptDetail,
  ExamAttemptListResponse,
  QuestionGenerationRequest,
  QuestionGenerationResponse,
  ExamStatistics,
  UserExamStatistics,
} from '../types';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const API_V1 = `${API_URL}/api/v1`;

// Create axios instance
const api = axios.create({
  baseURL: API_V1,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  login: async (credentials: LoginCredentials): Promise<AuthResponse> => {
    const response = await api.post<AuthResponse>('/auth/login', credentials);
    return response.data;
  },

  register: async (data: RegisterData): Promise<any> => {
    const response = await api.post('/auth/register', data);
    return response.data;
  },

  registerAdmin: async (data: RegisterData): Promise<any> => {
    const response = await api.post('/auth/admin/register', data);
    return response.data;
  },
};

// Videos API
export const videosAPI = {
  list: async (params?: {
    page?: number;
    page_size?: number;
    category_id?: number;
    search?: string;
  }): Promise<VideoListResponse> => {
    const response = await api.get<VideoListResponse>('/videos/', { params });
    return response.data;
  },

  get: async (id: number): Promise<Video> => {
    const response = await api.get<Video>(`/videos/${id}`);
    return response.data;
  },

  upload: async (data: VideoUploadData): Promise<Video> => {
    const formData = new FormData();
    formData.append('title', data.title);
    if (data.description) formData.append('description', data.description);
    if (data.category_id) formData.append('category_id', data.category_id.toString());
    if (data.tags) formData.append('tags', data.tags);
    formData.append('video_file', data.video_file);
    formData.append('transcript_file', data.transcript_file);

    const response = await api.post<Video>('/videos/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  update: async (
    id: number,
    data: Partial<Omit<Video, 'id' | 'created_at' | 'updated_at'>>
  ): Promise<Video> => {
    const response = await api.put<Video>(`/videos/${id}`, data);
    return response.data;
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/videos/${id}`);
  },
};

// Progress API
export const progressAPI = {
  update: async (data: ProgressUpdate): Promise<LearningProgress> => {
    const response = await api.post<LearningProgress>('/progress/', data);
    return response.data;
  },

  getMyProgress: async (videoId?: number): Promise<LearningProgress[]> => {
    const params = videoId ? { video_id: videoId } : {};
    const response = await api.get<LearningProgress[]>('/progress/my-progress', {
      params,
    });
    return response.data;
  },

  getVideoStats: async (videoId: number): Promise<any> => {
    const response = await api.get(`/progress/video/${videoId}/stats`);
    return response.data;
  },
};

// Materials API
export const materialsAPI = {
  list: async (videoId: number): Promise<MaterialListResponse> => {
    const response = await api.get<MaterialListResponse>(`/videos/${videoId}/materials`);
    return response.data;
  },

  get: async (materialId: number): Promise<Material> => {
    const response = await api.get<Material>(`/materials/${materialId}`);
    return response.data;
  },

  upload: async (videoId: number, data: MaterialUploadData): Promise<Material> => {
    const formData = new FormData();
    if (data.title) formData.append('title', data.title);
    if (data.description) formData.append('description', data.description);
    formData.append('material_file', data.material_file);

    const response = await api.post<Material>(`/videos/${videoId}/materials`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  update: async (
    materialId: number,
    data: { title?: string; description?: string }
  ): Promise<Material> => {
    const response = await api.put<Material>(`/materials/${materialId}`, data);
    return response.data;
  },

  delete: async (materialId: number): Promise<void> => {
    await api.delete(`/materials/${materialId}`);
  },
};

// Chat API
export const chatAPI = {
  askQuestion: async (data: AskQuestionRequest): Promise<AskQuestionResponse> => {
    const response = await api.post<AskQuestionResponse>('/chat/ask', data);
    return response.data;
  },

  listSessions: async (params?: {
    video_id?: number;
    page?: number;
    page_size?: number;
  }): Promise<ChatSessionListResponse> => {
    const response = await api.get<ChatSessionListResponse>('/chat/sessions', { params });
    return response.data;
  },

  getSession: async (sessionId: number): Promise<ChatSession> => {
    const response = await api.get<ChatSession>(`/chat/sessions/${sessionId}`);
    return response.data;
  },

  deleteSession: async (sessionId: number): Promise<void> => {
    await api.delete(`/chat/sessions/${sessionId}`);
  },

  exportSession: async (sessionId: number): Promise<{ message: string; s3_url: string }> => {
    const response = await api.post<{ message: string; s3_url: string }>(
      `/chat/sessions/${sessionId}/export`
    );
    return response.data;
  },

  processTranscript: async (videoId: number): Promise<any> => {
    const response = await api.post(`/chat/process-transcript/${videoId}`);
    return response.data;
  },

  getCollectionInfo: async (videoId: number): Promise<any> => {
    const response = await api.get(`/chat/collection-info/${videoId}`);
    return response.data;
  },

  generateQuiz: async (data: GenerateQuizRequest): Promise<GenerateQuizResponse> => {
    const response = await api.post<GenerateQuizResponse>('/chat/generate-quiz', data);
    return response.data;
  },
};

// Agora Voice AI API
export const agoraAPI = {
  generateToken: async (params?: { channel?: string; uid?: number }): Promise<GenerateTokenResponse> => {
    const response = await api.get<GenerateTokenResponse>('/agora/generate-token', { params });
    return response.data;
  },

  inviteAgent: async (data: InviteAgentRequest): Promise<InviteAgentResponse> => {
    const response = await api.post<InviteAgentResponse>('/agora/invite-agent', data);
    return response.data;
  },

  stopConversation: async (data: StopConversationRequest): Promise<{ status: string; agent_id: string }> => {
    const response = await api.post<{ status: string; agent_id: string }>('/agora/stop-conversation', data);
    return response.data;
  },
};

// Prompts API
export const promptsAPI = {
  list: async (params?: {
    page?: number;
    page_size?: number;
    category?: string;
    active_only?: boolean;
  }): Promise<PromptTemplateListResponse> => {
    const response = await api.get<PromptTemplateListResponse>('/prompts/', { params });
    return response.data;
  },

  getById: async (id: number): Promise<PromptTemplate> => {
    const response = await api.get<PromptTemplate>(`/prompts/${id}`);
    return response.data;
  },

  getByName: async (name: string): Promise<PromptTemplate> => {
    const response = await api.get<PromptTemplate>(`/prompts/name/${name}`);
    return response.data;
  },

  create: async (data: PromptTemplateCreate): Promise<PromptTemplate> => {
    const response = await api.post<PromptTemplate>('/prompts/', data);
    return response.data;
  },

  update: async (id: number, data: PromptTemplateUpdate): Promise<PromptTemplate> => {
    const response = await api.put<PromptTemplate>(`/prompts/${id}`, data);
    return response.data;
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/prompts/${id}`);
  },

  render: async (data: PromptRenderRequest): Promise<PromptRenderResponse> => {
    const response = await api.post<PromptRenderResponse>('/prompts/render', data);
    return response.data;
  },

  getByCategory: async (category: string): Promise<PromptTemplate[]> => {
    const response = await api.get<PromptTemplate[]>(`/prompts/category/${category}`);
    return response.data;
  },
};

// Users API
export const usersAPI = {
  list: async (params?: {
    page?: number;
    page_size?: number;
    search?: string;
    is_active?: boolean;
    is_admin?: boolean;
  }): Promise<UserListResponse> => {
    const response = await api.get<UserListResponse>('/users/', { params });
    return response.data;
  },

  getById: async (id: number): Promise<UserDetailResponse> => {
    const response = await api.get<UserDetailResponse>(`/users/${id}`);
    return response.data;
  },

  create: async (data: UserCreateData, is_admin?: boolean): Promise<UserDetailResponse> => {
    const params = is_admin !== undefined ? { is_admin } : {};
    const response = await api.post<UserDetailResponse>('/users/', data, { params });
    return response.data;
  },

  update: async (id: number, data: UserUpdateData): Promise<UserDetailResponse> => {
    const response = await api.put<UserDetailResponse>(`/users/${id}`, data);
    return response.data;
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/users/${id}`);
  },

  activate: async (id: number): Promise<UserDetailResponse> => {
    const response = await api.post<UserDetailResponse>(`/users/${id}/activate`);
    return response.data;
  },

  getProgress: async (id: number): Promise<LearningProgress[]> => {
    const response = await api.get<LearningProgress[]>(`/users/${id}/progress`);
    return response.data;
  },

  getChatSessions: async (id: number): Promise<ChatSession[]> => {
    const response = await api.get<ChatSession[]>(`/users/${id}/chat-sessions`);
    return response.data;
  },
};

// Categories API
export const categoriesAPI = {
  list: async (params?: { include_inactive?: boolean }): Promise<VideoCategory[]> => {
    const response = await api.get<VideoCategory[]>('/categories/', { params });
    return response.data;
  },

  getTree: async (params?: { include_inactive?: boolean }): Promise<VideoCategoryTree[]> => {
    const response = await api.get<VideoCategoryTree[]>('/categories/tree', { params });
    return response.data;
  },

  getById: async (id: number): Promise<VideoCategory> => {
    const response = await api.get<VideoCategory>(`/categories/${id}`);
    return response.data;
  },

  create: async (data: VideoCategoryCreate): Promise<VideoCategory> => {
    const response = await api.post<VideoCategory>('/categories/', data);
    return response.data;
  },

  update: async (id: number, data: VideoCategoryUpdate): Promise<VideoCategory> => {
    const response = await api.put<VideoCategory>(`/categories/${id}`, data);
    return response.data;
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/categories/${id}`);
  },
};

// Statistics API
export const statisticsAPI = {
  getOverview: async (): Promise<SystemOverview> => {
    const response = await api.get<SystemOverview>('/statistics/overview');
    return response.data;
  },

  getUserStats: async (userId: number): Promise<UserStatistics> => {
    const response = await api.get<UserStatistics>(`/statistics/users/${userId}`);
    return response.data;
  },

  getVideoStats: async (videoId: number): Promise<VideoStatistics> => {
    const response = await api.get<VideoStatistics>(`/statistics/videos/${videoId}`);
    return response.data;
  },

  getCategoryStats: async (categoryId: number): Promise<CategoryStatistics> => {
    const response = await api.get<CategoryStatistics>(`/statistics/categories/${categoryId}`);
    return response.data;
  },

  getPopular: async (days: number = 30): Promise<PopularContent> => {
    const response = await api.get<PopularContent>('/statistics/popular', { params: { days } });
    return response.data;
  },
};

// Exam Management API
export const examAPI = {
  // Exam CRUD (Admin)
  createExam: async (data: ExamCreate): Promise<Exam> => {
    const response = await api.post<Exam>('/exams/', data);
    return response.data;
  },

  listExams: async (params?: {
    page?: number;
    page_size?: number;
    search?: string;
    status_filter?: string;
  }): Promise<ExamListResponse> => {
    const response = await api.get<ExamListResponse>('/exams/', { params });
    return response.data;
  },

  getExam: async (examId: number): Promise<Exam> => {
    const response = await api.get<Exam>(`/exams/${examId}`);
    return response.data;
  },

  updateExam: async (examId: number, data: ExamUpdate): Promise<Exam> => {
    const response = await api.put<Exam>(`/exams/${examId}`, data);
    return response.data;
  },

  deleteExam: async (examId: number): Promise<void> => {
    await api.delete(`/exams/${examId}`);
  },

  // Question Management (Admin)
  addQuestion: async (examId: number, data: ExamQuestionCreate): Promise<ExamQuestion> => {
    const response = await api.post<ExamQuestion>(`/exams/${examId}/questions`, data);
    return response.data;
  },

  updateQuestion: async (questionId: number, data: ExamQuestionUpdate): Promise<ExamQuestion> => {
    const response = await api.put<ExamQuestion>(`/exams/questions/${questionId}`, data);
    return response.data;
  },

  deleteQuestion: async (questionId: number): Promise<void> => {
    await api.delete(`/exams/questions/${questionId}`);
  },

  // AI Question Generation (Admin)
  generateQuestions: async (data: QuestionGenerationRequest): Promise<QuestionGenerationResponse> => {
    const response = await api.post<QuestionGenerationResponse>('/exams/generate-questions', data);
    return response.data;
  },

  addGeneratedQuestions: async (examId: number, questions: ExamQuestionCreate[]): Promise<Exam> => {
    const response = await api.post<Exam>(`/exams/${examId}/add-generated-questions`, questions);
    return response.data;
  },

  // Public Exam Taking (No Auth)
  getPublicExam: async (examId: number): Promise<ExamPublic> => {
    const response = await api.get<ExamPublic>(`/exams/public/${examId}`);
    return response.data;
  },

  startAttempt: async (data: ExamAttemptCreate): Promise<ExamAttempt> => {
    const response = await api.post<ExamAttempt>('/exams/public/start', data);
    return response.data;
  },

  submitAttempt: async (attemptId: number, data: ExamAttemptSubmit): Promise<ExamAttemptDetail> => {
    const response = await api.post<ExamAttemptDetail>(`/exams/public/submit/${attemptId}`, data);
    return response.data;
  },

  // Results & Analytics (Admin)
  listExamAttempts: async (examId: number, params?: {
    page?: number;
    page_size?: number;
  }): Promise<ExamAttemptListResponse> => {
    const response = await api.get<ExamAttemptListResponse>(`/exams/${examId}/attempts`, { params });
    return response.data;
  },

  getAttemptDetails: async (attemptId: number): Promise<ExamAttemptDetail> => {
    const response = await api.get<ExamAttemptDetail>(`/exams/attempts/${attemptId}`);
    return response.data;
  },

  getExamStatistics: async (examId: number): Promise<ExamStatistics> => {
    const response = await api.get<ExamStatistics>(`/exams/${examId}/statistics`);
    return response.data;
  },

  getUserExamStatistics: async (userEmail: string): Promise<UserExamStatistics> => {
    const response = await api.get<UserExamStatistics>(`/exams/users/${userEmail}/statistics`);
    return response.data;
  },
};

export default api;
