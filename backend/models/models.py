from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Integer, Float, JSON, Boolean, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from core.database import Base
import uuid


def generate_uuid():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    auth0_id = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    name = Column(String)
    picture = Column(String)
    role = Column(String, default="user")  # user, admin
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    agents = relationship("Agent", back_populates="user", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")


class Agent(Base):
    __tablename__ = "agents"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    system_prompt = Column(Text)
    personality = Column(String)  # professional, friendly, technical, etc.
    expertise = Column(String)  # RAG, LangChain, Prompting, etc.
    model = Column(String, default="gpt-4-1106-preview")
    temperature = Column(Float, default=0.7)
    max_tokens = Column(Integer, default=4096)
    top_k_retrieval = Column(Integer, default=5)
    is_active = Column(Boolean, default=True)
    metadata_ = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="agents")
    documents = relationship("Document", back_populates="agent", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="agent", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("idx_agent_user_id", "user_id"),
        Index("idx_agent_name", "name"),
    )


class Document(Base):
    __tablename__ = "documents"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    agent_id = Column(String, ForeignKey("agents.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String, nullable=False)
    file_type = Column(String)  # pdf, docx, txt
    file_size = Column(Integer)  # bytes
    s3_key = Column(String, nullable=False)
    s3_url = Column(String)
    num_chunks = Column(Integer, default=0)
    status = Column(String, default="pending")  # pending, processing, completed, failed
    error_message = Column(Text)
    metadata_ = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    agent = relationship("Agent", back_populates="documents")
    
    # Indexes
    __table_args__ = (
        Index("idx_document_agent_id", "agent_id"),
        Index("idx_document_status", "status"),
    )


class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    agent_id = Column(String, ForeignKey("agents.id", ondelete="CASCADE"), nullable=False)
    title = Column(String)
    is_active = Column(Boolean, default=True)
    metadata_ = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    agent = relationship("Agent", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("idx_conversation_user_id", "user_id"),
        Index("idx_conversation_agent_id", "agent_id"),
    )


class Message(Base):
    __tablename__ = "messages"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    conversation_id = Column(String, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    role = Column(String, nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    retrieved_chunks = Column(JSON)  # List of retrieved document chunks
    tokens_used = Column(Integer)
    latency_ms = Column(Float)
    metadata_ = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    evaluation = relationship("Evaluation", back_populates="message", uselist=False, cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("idx_message_conversation_id", "conversation_id"),
        Index("idx_message_created_at", "created_at"),
    )


class Evaluation(Base):
    __tablename__ = "evaluations"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    message_id = Column(String, ForeignKey("messages.id", ondelete="CASCADE"), unique=True, nullable=False)
    groundedness_score = Column(Float)
    faithfulness_score = Column(Float)
    answer_correctness_score = Column(Float)
    answer_relevancy_score = Column(Float)
    context_precision_score = Column(Float)
    context_recall_score = Column(Float)
    overall_score = Column(Float)
    evaluation_details = Column(JSON)
    status = Column(String, default="pending")  # pending, completed, failed
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    message = relationship("Message", back_populates="evaluation")
    
    # Indexes
    __table_args__ = (
        Index("idx_evaluation_message_id", "message_id"),
        Index("idx_evaluation_overall_score", "overall_score"),
    )


class PromptSuggestion(Base):
    __tablename__ = "prompt_suggestions"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    original_prompt = Column(Text, nullable=False)
    improved_prompt = Column(Text, nullable=False)
    improvements = Column(JSON)  # List of improvement suggestions
    category = Column(String)  # clarity, specificity, structure, etc.
    rating = Column(Integer)  # User feedback 1-5
    metadata_ = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Indexes
    __table_args__ = (
        Index("idx_prompt_user_id", "user_id"),
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"))
    action = Column(String, nullable=False)  # create_agent, upload_document, chat, etc.
    resource_type = Column(String)  # agent, document, conversation
    resource_id = Column(String)
    details = Column(JSON)
    ip_address = Column(String)
    user_agent = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Indexes
    __table_args__ = (
        Index("idx_audit_user_id", "user_id"),
        Index("idx_audit_action", "action"),
        Index("idx_audit_created_at", "created_at"),
    )
