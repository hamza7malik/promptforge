from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List

from core.database import get_db
from core.auth import get_current_user_id
from models.models import User, Agent
from schemas.schemas import AgentCreate, AgentUpdate, AgentResponse
from core.logging import logger

router = APIRouter()


@router.post("/", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    agent_data: AgentCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Create a new agent"""
    try:
        # Ensure user exists
        user_result = await db.execute(select(User).where(User.auth0_id == user_id))
        user = user_result.scalar_one_or_none()
        
        if not user:
            # Create user if doesn't exist
            user = User(auth0_id=user_id, email=user_id)
            db.add(user)
            await db.flush()
        
        # Create agent
        agent = Agent(
            user_id=user.id,
            **agent_data.model_dump()
        )
        db.add(agent)
        await db.commit()
        await db.refresh(agent)
        
        logger.info(f"Created agent: {agent.id}", agent_name=agent.name, user_id=user_id)
        
        return agent
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating agent: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create agent"
        )


@router.get("/", response_model=List[AgentResponse])
async def list_agents(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """List all agents for current user"""
    try:
        # Get user
        user_result = await db.execute(select(User).where(User.auth0_id == user_id))
        user = user_result.scalar_one_or_none()
        
        if not user:
            return []
        
        # Get agents with document count
        from models.models import Document
        query = (
            select(
                Agent,
                func.count(Document.id).label("document_count")
            )
            .outerjoin(Document)
            .where(Agent.user_id == user.id)
            .group_by(Agent.id)
            .offset(skip)
            .limit(limit)
        )
        
        result = await db.execute(query)
        agents_with_counts = result.all()
        
        agents_response = []
        for agent, doc_count in agents_with_counts:
            agent_dict = AgentResponse.model_validate(agent).model_dump()
            agent_dict["document_count"] = doc_count
            agents_response.append(agent_dict)
        
        return agents_response
    except Exception as e:
        logger.error(f"Error listing agents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list agents"
        )


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get specific agent"""
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
        
        return agent
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get agent"
        )


@router.patch("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: str,
    agent_update: AgentUpdate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Update agent"""
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
        
        # Update fields
        update_data = agent_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(agent, field, value)
        
        await db.commit()
        await db.refresh(agent)
        
        logger.info(f"Updated agent: {agent_id}")
        
        return agent
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating agent: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update agent"
        )


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Delete agent and all associated data"""
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
        
        # Delete agent (cascade will handle documents, conversations, etc.)
        await db.delete(agent)
        await db.commit()
        
        # TODO: Delete from vector store
        # from services.rag.pipeline import rag_pipeline
        # await rag_pipeline.vector_store.delete_namespace(agent_id)
        
        logger.info(f"Deleted agent: {agent_id}")
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting agent: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete agent"
        )
