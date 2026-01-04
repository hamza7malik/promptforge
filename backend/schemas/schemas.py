from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# Enums
class AgentPersonality(str, Enum):
    PROFESSIONAL = "professional"
    FRIENDLY = "friendly"
    TECHNICAL = "technical"
    CREATIVE = "creative"
    ANALYTICAL = "analytical"


class DocumentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


# Base Schemas
class UserBase(BaseModel):
    email: str
    name: Optional[str] = None
    picture: Optional[str] = None


class UserCreate(UserBase):
    auth0_id: str


class UserResponse(UserBase):
    id: str
    auth0_id: str
    role: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


# Agent Schemas
class AgentBase(BaseModel):
    name: str
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    personality: Optional[AgentPersonality] = AgentPersonality.PROFESSIONAL
    expertise: Optional[str] = None
    model: str = "gpt-4-1106-preview"
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4096, ge=1, le=128000)
    top_k_retrieval: int = Field(default=5, ge=1, le=20)


class AgentCreate(AgentBase):
    pass


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    personality: Optional[AgentPersonality] = None
    expertise: Optional[str] = None
    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, ge=1, le=128000)
    top_k_retrieval: Optional[int] = Field(default=None, ge=1, le=20)
    is_active: Optional[bool] = None


class AgentResponse(AgentBase):
    id: str
    user_id: str
    is_active: bool
    metadata_: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: Optional[datetime] = None
    document_count: Optional[int] = 0
    
    model_config = ConfigDict(from_attributes=True)


# Document Schemas
class DocumentBase(BaseModel):
    filename: str
    file_type: Optional[str] = None


class DocumentCreate(DocumentBase):
    agent_id: str
    s3_key: str
    file_size: Optional[int] = None


class DocumentResponse(DocumentBase):
    id: str
    agent_id: str
    s3_key: str
    s3_url: Optional[str] = None
    file_size: Optional[int] = None
    num_chunks: int
    status: DocumentStatus
    error_message: Optional[str] = None
    metadata_: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


# Conversation Schemas
class ConversationBase(BaseModel):
    title: Optional[str] = None


class ConversationCreate(ConversationBase):
    agent_id: str


class ConversationResponse(ConversationBase):
    id: str
    user_id: str
    agent_id: str
    is_active: bool
    metadata_: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: Optional[datetime] = None
    message_count: Optional[int] = 0
    
    model_config = ConfigDict(from_attributes=True)


# Message Schemas
class RetrievedChunk(BaseModel):
    content: str
    score: float
    document_id: str
    document_name: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MessageBase(BaseModel):
    content: str


class MessageCreate(MessageBase):
    conversation_id: str
    role: MessageRole = MessageRole.USER


class MessageResponse(MessageBase):
    id: str
    conversation_id: str
    role: MessageRole
    retrieved_chunks: Optional[List[RetrievedChunk]] = None
    tokens_used: Optional[int] = None
    latency_ms: Optional[float] = None
    metadata_: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Chat Schemas
class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    stream: bool = True


class ChatResponse(BaseModel):
    message_id: str
    conversation_id: str
    content: str
    retrieved_chunks: Optional[List[RetrievedChunk]] = None
    tokens_used: Optional[int] = None
    latency_ms: Optional[float] = None


# Evaluation Schemas
class EvaluationResponse(BaseModel):
    id: str
    message_id: str
    groundedness_score: Optional[float] = None
    faithfulness_score: Optional[float] = None
    answer_correctness_score: Optional[float] = None
    answer_relevancy_score: Optional[float] = None
    context_precision_score: Optional[float] = None
    context_recall_score: Optional[float] = None
    overall_score: Optional[float] = None
    evaluation_details: Optional[Dict[str, Any]] = None
    status: str
    error_message: Optional[str] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Prompt Suggestion Schemas
class PromptSuggestionRequest(BaseModel):
    prompt: str
    context: Optional[str] = None


class Improvement(BaseModel):
    type: str
    description: str
    example: Optional[str] = None


class PromptSuggestionResponse(BaseModel):
    id: str
    original_prompt: str
    improved_prompt: str
    improvements: List[Improvement]
    category: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# File Upload Schemas
class PresignedUploadRequest(BaseModel):
    filename: str
    file_type: str
    file_size: int


class PresignedUploadResponse(BaseModel):
    upload_url: str
    s3_key: str
    fields: Dict[str, str]


# Admin Schemas
class UsageStats(BaseModel):
    total_users: int
    total_agents: int
    total_documents: int
    total_conversations: int
    total_messages: int
    tokens_used_today: int
    tokens_used_month: int


class VectorStats(BaseModel):
    index_name: str
    dimension: int
    total_vectors: int
    namespaces: List[str]


class SystemHealth(BaseModel):
    status: str
    database: str
    vector_db: str
    storage: str
    llm: str
    timestamp: datetime
