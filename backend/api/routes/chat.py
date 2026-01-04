from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import AsyncGenerator
import json
import time

from core.database import get_db
from core.auth import get_current_user_id
from models.models import User, Agent, Conversation, Message
from schemas.schemas import ChatRequest, ChatResponse, RetrievedChunk
from services.rag.pipeline import rag_pipeline
from services.llm.service import llm_service
from core.logging import logger

router = APIRouter()


async def stream_chat_response(
    agent: Agent,
    conversation_id: str,
    message_content: str,
    db: AsyncSession
) -> AsyncGenerator[str, None]:
    """Stream chat response with SSE format"""
    try:
        start_time = time.time()
        
        # Retrieve context from RAG
        context_chunks = await rag_pipeline.retrieve_context(
            query=message_content,
            agent_id=agent.id,
            top_k=agent.top_k_retrieval
        )
        
        # Get conversation history
        history_result = await db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(20)
        )
        messages = history_result.scalars().all()
        conversation_history = [
            {"role": msg.role, "content": msg.content}
            for msg in reversed(messages)
        ]
        
        # Send metadata first
        metadata = {
            "type": "metadata",
            "retrieved_chunks": [
                {
                    "content": chunk["content"][:200] + "...",
                    "score": chunk["score"],
                    "document_name": chunk["document_name"]
                }
                for chunk in context_chunks
            ]
        }
        yield f"data: {json.dumps(metadata)}\n\n"
        
        # Stream LLM response
        full_response = ""
        async for chunk in llm_service.generate_response(
            query=message_content,
            context_chunks=context_chunks,
            system_prompt=agent.system_prompt or f"You are {agent.name}, an expert AI assistant.",
            conversation_history=conversation_history,
            temperature=agent.temperature,
            max_tokens=agent.max_tokens
        ):
            full_response += chunk
            yield f"data: {json.dumps({'type': 'content', 'content': chunk})}\n\n"
        
        # Calculate metrics
        elapsed_ms = (time.time() - start_time) * 1000
        from services.llm.service import LLMService
        llm_svc = LLMService()
        token_count = len(llm_svc.encoding.encode(full_response))
        
        # Save assistant message
        assistant_message = Message(
            conversation_id=conversation_id,
            role="assistant",
            content=full_response,
            retrieved_chunks=[
                {
                    "content": chunk["content"],
                    "score": chunk["score"],
                    "document_id": chunk["document_id"],
                    "document_name": chunk["document_name"]
                }
                for chunk in context_chunks
            ],
            tokens_used=token_count,
            latency_ms=elapsed_ms
        )
        db.add(assistant_message)
        await db.commit()
        await db.refresh(assistant_message)
        
        # Send completion metadata
        completion = {
            "type": "done",
            "message_id": assistant_message.id,
            "tokens_used": token_count,
            "latency_ms": elapsed_ms
        }
        yield f"data: {json.dumps(completion)}\n\n"
        
    except Exception as e:
        logger.error(f"Error in chat stream: {e}")
        error_data = {"type": "error", "error": str(e)}
        yield f"data: {json.dumps(error_data)}\n\n"


@router.post("/{agent_id}")
async def chat_with_agent(
    agent_id: str,
    request: ChatRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Chat with an agent (streaming or non-streaming)"""
    try:
        # Get user
        user_result = await db.execute(select(User).where(User.auth0_id == user_id))
        user = user_result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        # Get agent
        agent_result = await db.execute(
            select(Agent).where(Agent.id == agent_id, Agent.user_id == user.id)
        )
        agent = agent_result.scalar_one_or_none()
        
        if not agent:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
        
        # Get or create conversation
        if request.conversation_id:
            conv_result = await db.execute(
                select(Conversation).where(
                    Conversation.id == request.conversation_id,
                    Conversation.user_id == user.id
                )
            )
            conversation = conv_result.scalar_one_or_none()
            if not conversation:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
        else:
            # Create new conversation
            conversation = Conversation(
                user_id=user.id,
                agent_id=agent_id,
                title=request.message[:50] + "..." if len(request.message) > 50 else request.message
            )
            db.add(conversation)
            await db.commit()
            await db.refresh(conversation)
        
        # Save user message
        user_message = Message(
            conversation_id=conversation.id,
            role="user",
            content=request.message
        )
        db.add(user_message)
        await db.commit()
        
        # Return streaming or non-streaming response
        if request.stream:
            return StreamingResponse(
                stream_chat_response(agent, conversation.id, request.message, db),
                media_type="text/event-stream"
            )
        else:
            # Non-streaming response
            start_time = time.time()
            
            # Retrieve context
            context_chunks = await rag_pipeline.retrieve_context(
                query=request.message,
                agent_id=agent.id,
                top_k=agent.top_k_retrieval
            )
            
            # Get conversation history
            history_result = await db.execute(
                select(Message)
                .where(Message.conversation_id == conversation.id)
                .order_by(Message.created_at.desc())
                .limit(20)
            )
            messages = history_result.scalars().all()
            conversation_history = [
                {"role": msg.role, "content": msg.content}
                for msg in reversed(messages)
            ]
            
            # Generate response
            response_text, token_count, latency_ms = await llm_service.generate_response_non_streaming(
                query=request.message,
                context_chunks=context_chunks,
                system_prompt=agent.system_prompt or f"You are {agent.name}, an expert AI assistant.",
                conversation_history=conversation_history,
                temperature=agent.temperature,
                max_tokens=agent.max_tokens
            )
            
            # Save assistant message
            assistant_message = Message(
                conversation_id=conversation.id,
                role="assistant",
                content=response_text,
                retrieved_chunks=[
                    {
                        "content": chunk["content"],
                        "score": chunk["score"],
                        "document_id": chunk["document_id"],
                        "document_name": chunk["document_name"]
                    }
                    for chunk in context_chunks
                ],
                tokens_used=token_count,
                latency_ms=latency_ms
            )
            db.add(assistant_message)
            await db.commit()
            await db.refresh(assistant_message)
            
            return ChatResponse(
                message_id=assistant_message.id,
                conversation_id=conversation.id,
                content=response_text,
                retrieved_chunks=[
                    RetrievedChunk(**chunk) for chunk in context_chunks
                ],
                tokens_used=token_count,
                latency_ms=latency_ms
            )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in chat: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process chat"
        )
