import axios, { AxiosInstance } from "axios";
import {
  Agent,
  AgentCreate,
  AgentUpdate,
  Document,
  Conversation,
  Message,
  ChatRequest,
  ChatResponse,
  Evaluation,
  PromptSuggestion,
  PresignedUploadRequest,
  PresignedUploadResponse,
  UsageStats,
  VectorStats,
  SystemHealth,
} from "@/types";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

class APIClient {
  private client: AxiosInstance;
  private tokenProvider: (() => Promise<string>) | null = null;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        "Content-Type": "application/json",
      },
    });

    // Request interceptor to add auth token
    this.client.interceptors.request.use(async (config) => {
      if (this.tokenProvider) {
        const token = await this.tokenProvider();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
      }
      return config;
    });

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        console.error("API Error:", error.response?.data || error.message);
        throw error;
      }
    );
  }

  setTokenProvider(provider: () => Promise<string>) {
    this.tokenProvider = provider;
  }

  // Agents
  async createAgent(data: AgentCreate): Promise<Agent> {
    const response = await this.client.post("/api/agents/", data);
    return response.data;
  }

  async listAgents(): Promise<Agent[]> {
    const response = await this.client.get("/api/agents/");
    return response.data;
  }

  async getAgent(agentId: string): Promise<Agent> {
    const response = await this.client.get(`/api/agents/${agentId}`);
    return response.data;
  }

  async updateAgent(agentId: string, data: AgentUpdate): Promise<Agent> {
    const response = await this.client.patch(`/api/agents/${agentId}`, data);
    return response.data;
  }

  async deleteAgent(agentId: string): Promise<void> {
    await this.client.delete(`/api/agents/${agentId}`);
  }

  // Documents
  async getPresignedUploadUrl(
    data: PresignedUploadRequest
  ): Promise<PresignedUploadResponse> {
    const response = await this.client.post(
      "/api/documents/presigned-upload",
      data
    );
    return response.data;
  }

  async createDocument(data: {
    agent_id: string;
    filename: string;
    file_type: string;
    s3_key: string;
    file_size: number;
  }): Promise<Document> {
    const response = await this.client.post("/api/documents/", data);
    return response.data;
  }

  async listAgentDocuments(agentId: string): Promise<Document[]> {
    const response = await this.client.get(`/api/documents/agent/${agentId}`);
    return response.data;
  }

  async deleteDocument(documentId: string): Promise<void> {
    await this.client.delete(`/api/documents/${documentId}`);
  }

  // Chat
  async chatWithAgent(
    agentId: string,
    request: ChatRequest
  ): Promise<ChatResponse | ReadableStream> {
    if (request.stream) {
      // For streaming, return raw response
      const response = await fetch(`${API_BASE_URL}/api/chat/${agentId}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${await this.tokenProvider?.()}`,
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        throw new Error("Stream request failed");
      }

      return response.body!;
    } else {
      const response = await this.client.post(`/api/chat/${agentId}`, request);
      return response.data;
    }
  }

  // Conversations
  async createConversation(data: {
    agent_id: string;
    title?: string;
  }): Promise<Conversation> {
    const response = await this.client.post("/api/conversations/", data);
    return response.data;
  }

  async listConversations(): Promise<Conversation[]> {
    const response = await this.client.get("/api/conversations/");
    return response.data;
  }

  async getConversationMessages(conversationId: string): Promise<Message[]> {
    const response = await this.client.get(
      `/api/conversations/${conversationId}/messages`
    );
    return response.data;
  }

  async deleteConversation(conversationId: string): Promise<void> {
    await this.client.delete(`/api/conversations/${conversationId}`);
  }

  // Evaluations
  async evaluateMessage(messageId: string): Promise<Evaluation> {
    const response = await this.client.post(`/api/evaluations/${messageId}`);
    return response.data;
  }

  async getEvaluation(messageId: string): Promise<Evaluation> {
    const response = await this.client.get(`/api/evaluations/${messageId}`);
    return response.data;
  }

  // Prompts
  async suggestPromptImprovements(data: {
    prompt: string;
    context?: string;
  }): Promise<PromptSuggestion> {
    const response = await this.client.post("/api/prompts/suggest", data);
    return response.data;
  }

  // Admin
  async getUsageStats(): Promise<UsageStats> {
    const response = await this.client.get("/api/admin/stats/usage");
    return response.data;
  }

  async getVectorStats(): Promise<VectorStats> {
    const response = await this.client.get("/api/admin/stats/vector");
    return response.data;
  }

  async getSystemHealth(): Promise<SystemHealth> {
    const response = await this.client.get("/api/admin/health");
    return response.data;
  }
}

export const apiClient = new APIClient();
