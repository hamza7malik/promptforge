from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta

from core.database import get_db
from core.auth import get_current_user_id
from models.models import User, Agent, Document, Conversation, Message
from schemas.schemas import UsageStats, VectorStats, SystemHealth
from services.rag.pipeline import rag_pipeline
from core.logging import logger

router = APIRouter()


async def verify_admin(user_id: str, db: AsyncSession):
    """Verify user has admin role"""
    user_result = await db.execute(select(User).where(User.auth0_id == user_id))
    user = user_result.scalar_one_or_none()
    
    if not user or user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return user


@router.get("/stats/usage", response_model=UsageStats)
async def get_usage_stats(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get platform usage statistics (admin only)"""
    try:
        await verify_admin(user_id, db)
        
        # Count totals
        total_users = await db.scalar(select(func.count(User.id)))
        total_agents = await db.scalar(select(func.count(Agent.id)))
        total_documents = await db.scalar(select(func.count(Document.id)))
        total_conversations = await db.scalar(select(func.count(Conversation.id)))
        total_messages = await db.scalar(select(func.count(Message.id)))
        
        # Tokens used today
        today = datetime.utcnow().date()
        tokens_today = await db.scalar(
            select(func.sum(Message.tokens_used))
            .where(func.date(Message.created_at) == today)
        ) or 0
        
        # Tokens used this month
        month_start = datetime.utcnow().replace(day=1)
        tokens_month = await db.scalar(
            select(func.sum(Message.tokens_used))
            .where(Message.created_at >= month_start)
        ) or 0
        
        return UsageStats(
            total_users=total_users or 0,
            total_agents=total_agents or 0,
            total_documents=total_documents or 0,
            total_conversations=total_conversations or 0,
            total_messages=total_messages or 0,
            tokens_used_today=tokens_today,
            tokens_used_month=tokens_month
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting usage stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get usage stats"
        )


@router.get("/stats/vector", response_model=VectorStats)
async def get_vector_stats(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get vector database statistics (admin only)"""
    try:
        await verify_admin(user_id, db)
        
        # Get Pinecone stats
        stats = await rag_pipeline.vector_store.get_index_stats()
        
        return VectorStats(
            index_name=stats.get("index_name", "unknown"),
            dimension=stats.get("dimension", 0),
            total_vectors=stats.get("total_vector_count", 0),
            namespaces=list(stats.get("namespaces", {}).keys())
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting vector stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get vector stats"
        )


@router.get("/health", response_model=SystemHealth)
async def get_system_health(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get system health status (admin only)"""
    try:
        await verify_admin(user_id, db)
        
        health = {
            "status": "healthy",
            "database": "unknown",
            "vector_db": "unknown",
            "storage": "unknown",
            "llm": "unknown",
            "timestamp": datetime.utcnow()
        }
        
        # Check database
        try:
            await db.execute(select(1))
            health["database"] = "healthy"
        except:
            health["database"] = "unhealthy"
            health["status"] = "degraded"
        
        # Check vector DB
        try:
            await rag_pipeline.vector_store.get_index_stats()
            health["vector_db"] = "healthy"
        except:
            health["vector_db"] = "unhealthy"
            health["status"] = "degraded"
        
        # Check storage (S3)
        try:
            from services.storage.s3_service import s3_service
            # Simple check - just verify client exists
            if s3_service.s3_client:
                health["storage"] = "healthy"
        except:
            health["storage"] = "unhealthy"
            health["status"] = "degraded"
        
        # Check LLM
        try:
            from services.llm.service import llm_service
            if llm_service.model:
                health["llm"] = "healthy"
        except:
            health["llm"] = "unhealthy"
            health["status"] = "degraded"
        
        return SystemHealth(**health)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking system health: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check system health"
        )
