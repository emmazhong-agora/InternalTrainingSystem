export interface User {
  id: number;
  email: string;
  username: string;
  full_name?: string;
  is_active: boolean;
  is_admin: boolean;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface RegisterData {
  email: string;
  username: string;
  password: string;
  full_name?: string;
}

export interface Material {
  id: number;
  video_id: number;
  file_url: string;
  original_filename: string;
  file_type?: string;
  file_size?: number;
  title?: string;
  description?: string;
  uploaded_by?: number;
  created_at: string;
  updated_at?: string;
}

export interface Video {
  id: number;
  title: string;
  description?: string;
  video_url: string;
  transcript_url: string;
  thumbnail_url?: string;
  duration?: number;
  file_size?: number;
  category_id?: number;
  tags?: string;
  uploaded_by?: number;
  ai_summary?: string;
  ai_outline?: string;
  ai_key_terms?: string;
  vectorization_status: string;  // "pending" | "processing" | "completed" | "failed"
  vectorization_error?: string;
  vectorized_at?: string;
  materials?: Material[];
  created_at: string;
  updated_at?: string;
}

export interface VideoListResponse {
  total: number;
  page: number;
  page_size: number;
  videos: Video[];
}

export interface VideoCategory {
  id: number;
  name: string;
  description?: string;
  parent_id?: number;
  created_at: string;
}

export interface LearningProgress {
  id: number;
  user_id: number;
  video_id: number;
  current_timestamp: number;
  total_watch_time: number;
  completion_percentage: number;
  is_completed: boolean;
  last_accessed: string;
  created_at: string;
}

export interface ProgressUpdate {
  video_id: number;
  current_timestamp: number;
  completion_percentage: number;
  is_completed: boolean;
}

export interface VideoUploadData {
  title: string;
  description?: string;
  category_id?: number;
  tags?: string;
  video_file: File;
  transcript_file: File;
}

export interface MaterialUploadData {
  title?: string;
  description?: string;
  material_file: File;
}

export interface MaterialListResponse {
  total: number;
  materials: Material[];
}

// Chat types
export enum MessageRole {
  USER = "user",
  ASSISTANT = "assistant",
  SYSTEM = "system"
}

export interface TranscriptChunk {
  text: string;
  start_time: number;
  end_time: number;
  index: number;
}

export interface ChatMessage {
  id: number;
  session_id: number;
  role: MessageRole;
  content: string;
  transcript_references?: string;
  confidence_score?: number;
  created_at: string;
}

export interface ChatSession {
  id: number;
  user_id: number;
  video_id: number;
  title?: string;
  s3_url?: string;
  created_at: string;
  updated_at?: string;
  last_message_at: string;
  messages: ChatMessage[];
}

export interface ChatSessionListResponse {
  total: number;
  sessions: ChatSession[];
}

export interface AskQuestionRequest {
  session_id?: number;
  video_id: number;
  question: string;
  current_timestamp?: number;
}

export interface AskQuestionResponse {
  session_id: number;
  user_message: ChatMessage;
  assistant_message: ChatMessage;
  referenced_chunks?: TranscriptChunk[];
  context_prompt?: string;
}

export interface QuizQuestion {
  question: string;
  options: string[];
  correct_answer: number;
  explanation: string;
}

export interface GenerateQuizRequest {
  video_id: number;
  current_timestamp?: number;
  difficulty?: "easy" | "medium" | "hard";
}

export interface GenerateQuizResponse {
  quiz: QuizQuestion;
  context_timestamp?: number;
}

// Agora Voice AI types
export interface GenerateTokenRequest {
  channel?: string;
  uid?: number;
}

export interface GenerateTokenResponse {
  token: string;
  uid: number;
  channel: string;
  app_id: string;
}

export interface InviteAgentRequest {
  requester_id: number;
  channel_name: string;
  video_id?: number;  // Video ID to retrieve knowledge base context
  input_modalities?: string[];
  output_modalities?: string[];
  tts_vendor?: "microsoft" | "elevenlabs";
  voice_name?: string;
}

export interface InviteAgentResponse {
  agent_id: string;
  channel: string;
  status: string;
}

export interface StopConversationRequest {
  agent_id: string;
}

// Prompt Management types
export interface PromptTemplate {
  id: number;
  name: string;
  category: string;
  description?: string;
  system_message: string;
  user_message_template?: string;
  model: string;
  temperature: number;
  max_tokens: number;
  top_p?: number;
  variables?: string[];
  response_format?: string;
  response_schema?: any;
  version: string;
  is_active: boolean;
  is_default: boolean;
  created_by?: number;
  created_at: string;
  updated_at?: string;
  usage_count: number;
  last_used_at?: string;
}

export interface PromptTemplateCreate {
  name: string;
  category: string;
  description?: string;
  system_message: string;
  user_message_template?: string;
  model?: string;
  temperature?: number;
  max_tokens?: number;
  top_p?: number;
  variables?: string[];
  response_format?: string;
  response_schema?: any;
  version?: string;
  is_active?: boolean;
  is_default?: boolean;
}

export interface PromptTemplateUpdate {
  name?: string;
  category?: string;
  description?: string;
  system_message?: string;
  user_message_template?: string;
  model?: string;
  temperature?: number;
  max_tokens?: number;
  top_p?: number;
  variables?: string[];
  response_format?: string;
  response_schema?: any;
  version?: string;
  is_active?: boolean;
  is_default?: boolean;
}

export interface PromptTemplateListResponse {
  total: number;
  page: number;
  page_size: number;
  prompts: PromptTemplate[];
}

export interface PromptRenderRequest {
  prompt_name: string;
  variables: { [key: string]: any };
}

export interface PromptRenderResponse {
  prompt_name: string;
  system_message: string;
  user_message?: string;
  model: string;
  temperature: number;
  max_tokens: number;
  top_p?: number;
  response_format?: string;
  response_schema?: any;
}

// User Management types
export interface UserDetailResponse extends User {
  total_videos_watched: number;
  total_watch_time: number;  // in seconds
  videos_completed: number;
  chat_sessions_count: number;
  total_chat_messages: number;
  quizzes_taken: number;
  last_activity?: string;
}

export interface UserListResponse {
  total: number;
  page: number;
  page_size: number;
  users: UserDetailResponse[];
}

export interface UserCreateData {
  email: string;
  username: string;
  password: string;
  full_name?: string;
  is_admin?: boolean;
}

export interface UserUpdateData {
  email?: string;
  username?: string;
  full_name?: string;
  is_active?: boolean;
  is_admin?: boolean;
  password?: string;
}

// Category Management types
export interface VideoCategory {
  id: number;
  name: string;
  description?: string;
  parent_id?: number;
  icon?: string;
  sort_order: number;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

export interface VideoCategoryTree extends VideoCategory {
  children: VideoCategoryTree[];
  video_count: number;
}

export interface VideoCategoryCreate {
  name: string;
  description?: string;
  parent_id?: number;
  icon?: string;
  sort_order?: number;
  is_active?: boolean;
}

export interface VideoCategoryUpdate {
  name?: string;
  description?: string;
  parent_id?: number;
  icon?: string;
  sort_order?: number;
  is_active?: boolean;
}

// Statistics types
export interface SystemOverview {
  total_users: number;
  active_users: number;
  total_videos: number;
  total_categories: number;
  total_watch_hours: number;
  total_chat_sessions: number;
  total_chat_messages: number;
  total_activities: number;
}

export interface UserStatistics {
  user_id: number;
  username: string;
  email: string;
  is_admin: boolean;
  is_active: boolean;
  total_videos_watched: number;
  videos_completed: number;
  total_watch_time: number;
  average_completion_rate: number;
  chat_sessions_count: number;
  total_chat_messages: number;
  quiz_attempts: number;
  voice_sessions: number;
  first_activity?: string;
  last_activity?: string;
  days_active: number;
  favorite_categories: Array<{ category_name: string; video_count: number }>;
}

export interface VideoStatistics {
  video_id: number;
  title: string;
  category_name?: string;
  total_views: number;
  unique_viewers: number;
  total_watch_time: number;
  average_watch_time: number;
  completion_rate: number;
  completed_count: number;
  chat_sessions: number;
  quiz_attempts: number;
  first_viewed?: string;
  last_viewed?: string;
}

export interface CategoryStatistics {
  category_id: number;
  category_name: string;
  parent_name?: string;
  total_videos: number;
  total_subcategories: number;
  total_views: number;
  unique_viewers: number;
  total_watch_time: number;
  average_completion_rate: number;
  top_videos: Array<{ video_id: number; title: string; views: number }>;
}

export interface PopularContent {
  most_viewed_videos: Array<{ video_id: number; title: string; views: number }>;
  most_completed_videos: Array<{ video_id: number; title: string; completions: number }>;
  most_discussed_videos: Array<{ video_id: number; title: string; chat_sessions: number }>;
  popular_categories: Array<{ category_id: number; name: string; views: number }>;
}
