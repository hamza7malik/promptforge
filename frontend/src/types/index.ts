export interface Agent {
  id: string;
  user_id: string;
  name: string;
  description?: string;
  system_prompt?: string;
  personality?:
    | "professional"
    | "friendly"
    | "technical"
    | "creative"
    | "analytical";
  expertise?: string;
  model: string;
  temperature: number;
  max_tokens: number;
  top_k_retrieval: number;
  is_active: boolean;
  metadata_?: Record<string, any>;
  created_at: string;
  updated_at?: string;
  document_count?: number;
}

export interface AgentCreate {
  name: string;
  description?: string;
  system_prompt?: string;
  personality?:
    | "professional"
    | "friendly"
    | "technical"
    | "creative"
    | "analytical";
  expertise?: string;
  model?: string;
  temperature?: number;
  max_tokens?: number;
  top_k_retrieval?: number;
}

export interface AgentUpdate {
  name?: string;
  description?: string;
  system_prompt?: string;
  personality?:
    | "professional"
    | "friendly"
    | "technical"
    | "creative"
    | "analytical";
  expertise?: string;
  model?: string;
  temperature?: number;
  max_tokens?: number;
  top_k_retrieval?: number;
  is_active?: boolean;
}

export interface Document {
  id: string;
  agent_id: string;
  filename: string;
  file_type?: string;
  file_size?: number;
  s3_key: string;
  s3_url?: string;
  num_chunks: number;
  status: "pending" | "processing" | "completed" | "failed";
  error_message?: string;
  metadata_?: Record<string, any>;
  created_at: string;
  updated_at?: string;
}

export interface Conversation {
  id: string;
  user_id: string;
  agent_id: string;
  title?: string;
  is_active: boolean;
  metadata_?: Record<string, any>;
  created_at: string;
  updated_at?: string;
  message_count?: number;
}

export interface Message {
  id: string;
  conversation_id: string;
  role: "user" | "assistant" | "system";
  content: string;
  retrieved_chunks?: RetrievedChunk[];
  tokens_used?: number;
  latency_ms?: number;
  metadata_?: Record<string, any>;
  created_at: string;
}

export interface RetrievedChunk {
  content: string;
  score: number;
  document_id: string;
  document_name: string;
  metadata?: Record<string, any>;
}

export interface ChatRequest {
  message: string;
  conversation_id?: string;
  stream?: boolean;
}

export interface ChatResponse {
  message_id: string;
  conversation_id: string;
  content: string;
  retrieved_chunks?: RetrievedChunk[];
  tokens_used?: number;
  latency_ms?: number;
}

export interface Evaluation {
  id: string;
  message_id: string;
  groundedness_score?: number;
  faithfulness_score?: number;
  answer_correctness_score?: number;
  answer_relevancy_score?: number;
  context_precision_score?: number;
  context_recall_score?: number;
  overall_score?: number;
  evaluation_details?: Record<string, any>;
  status: string;
  error_message?: string;
  created_at: string;
}

export interface PromptSuggestion {
  id: string;
  original_prompt: string;
  improved_prompt: string;
  improvements: Improvement[];
  category: string;
  created_at: string;
}

export interface Improvement {
  type: string;
  description: string;
  example?: string;
}

export interface PresignedUploadRequest {
  agent_id: string;
  filename: string;
  file_type: string;
  file_size: number;
}

export interface PresignedUploadResponse {
  upload_url: string;
  s3_key: string;
  fields: Record<string, string>;
}

export interface UsageStats {
  total_users: number;
  total_agents: number;
  total_documents: number;
  total_conversations: number;
  total_messages: number;
  tokens_used_today: number;
  tokens_used_month: number;
}

export interface VectorStats {
  index_name: string;
  dimension: number;
  total_vectors: number;
  namespaces: string[];
}

export interface SystemHealth {
  status: string;
  database: string;
  vector_db: string;
  storage: string;
  llm: string;
  timestamp: string;
}
